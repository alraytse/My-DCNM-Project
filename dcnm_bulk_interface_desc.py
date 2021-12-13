#!/usr/bin/env python3
"""

python3 script

    Script grabs all switch/ints from the input_data and figures out what they're currently set to
    once it knows what it is set to it should update the description leaving the interface_policy as is.
    If the policy needs to be change then it should be done prior to running this bulk deploy.

NOTE:
    *Currently its been tested and works for trunk_host and access_host interface_policy.  If you need
     to add a description to any interface that isn't set to one of these two policies DO IT MANUALLY!!
    *This script will NOT update any interface that already has a interface description.  This is to help
     with possible issues of overwritting something when you weren't aware.

Csv Format
device,interface,description


TODO:
    *Figure out if more than trunk_host and access_host is needed.

"""
import json, sys, re, argparse
from pprint import pprint

try:
    from dcnm.core.session import Session
    from dcnm.core.dcnm_calls import get_connection, get_inventory
    from dcnm.core.dcnm_parsers import DeploymentTracker

    # from dcnm.jira.jira_calls import jira_get_connection, jira_create_ticket, jira_update_ticket
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://github.com/alraytse/DCNM_Core.git"
    )
    exit(1)


def get_ints(sess, input_data):
    """ Based on input_data go get the current policy for each interface, and return it into a list for use in the update.

    Args:   sess (obj) - is imported from main and is keeping track of the session connection to DCNM.
            input_data (list of dictionaries)
                example of input_data = [{"deviceName": "rlf05lab", "ifName":"Ethernet1/1", "DESC":"TEST_INT_DESC"},{"deviceName": "rlf05lab", "ifName":"Ethernet1/2", "DESC":"TEST_INT_DESC"}]      
    returns:
            final_dict (dict) this dictionary has the payload needed for the interface update POST call.
    """
    host_sn = {}
    final_list = []
    exist_list = []
    inventory = get_inventory(sess, sess.fabric)
    for x in inventory:
        x = x.split(",")
        host_sn[x[0]] = x[3]
    for x in input_data:
        get_url = f"/rest/interface?serialNumber={host_sn[x['deviceName']]}&ifName={x['ifName']}"
        resp = sess.get(get_url)
        data = json.loads(resp.text)
        if resp.ok:
            for entry in data:
                if len(entry["interfaces"][0]["nvPairs"]["DESC"]) == 0:
                    # No int description exist update the key DESC with x['DESC']
                    entry["interfaces"][0]["nvPairs"]["DESC"] = f"{x['DESC']}"
                    final_list.append(entry)
                else:
                    exist_list.append(
                        f"{x['deviceName']}:{entry['interfaces'][0]['nvPairs']['INTF_NAME']}"
                    )
    return final_list, exist_list


def change_int_policy(sess, input_data):
    """ Function takes in input_data and cleans up the dictionary making it true json in the way DCNM expects it.  Adding a few k,v pairs as required
        by DCNM in the POST calls.
    
    Args: sess (obj) - is imported from main and is keeping track of the session connection to DCNM.
          input_data (list of dictionaries)
            example of input_data = [{'policy': 'access_host', 'interfaces': [{'serialNumber': 'FDO22222TLA', 'ifName': 'Ethernet1/2', 'nvPairs': {'BPDUGUARD_ENABLED': 'true', 'ADMIN_STATE': 'true', 'FABRIC_NAME': 'PDC1-LAB-Fabric', 'DESC': 'Eth1-2_Description', 'INTF_NAME': 'Ethernet1/2', 'PORTTYPE_FAST_ENABLED': 'true', 'MTU': 'jumbo'}}]}]
    
    returns:
            Boolean True for success or False for failed.
    """
    deploy_data = []
    change_failed = []
    # these urls maybe able to be updated. They work in both 10.4(2) and 11.0(1) however looks like 11+ uses
    # /rest/interface
    change_url = "/rest/globalInterface/pti"
    dep_url = "/rest/globalInterface/deploy"
    for x in input_data:
        # Adding two k,v pairs that DCNM requires eventhough aren't supplied by a get_int() function.
        x["interfaces"][0]["fabricName"] = f"{sess.fabric}"
        x["interfaces"][0]["interfaceType"] = "INTERFACE_ETHERNET"
        # DCNM is very picky with the json its receiving, this is changing dict.values equal to 'true' or 'false' to python True or False
        # Before we can json.dumps the data and make them json true or false.
        for k, v in x["interfaces"][0]["nvPairs"].items():
            if "true" in v:
                x["interfaces"][0]["nvPairs"][k] = True
            elif "false" in v:
                x["interfaces"][0]["nvPairs"][k] = False
        # if the key FABRIC_NAME is in nvPairs dictionary remove it as it causes HTTP POST to error out.
        # Again because DCNM respond swith this k,v in the wrong place during the get_int() function.
        if "FABRIC_NAME" in x["interfaces"][0]["nvPairs"].keys():
            del x["interfaces"][0]["nvPairs"]["FABRIC_NAME"]
        resp = sess.post(change_url, json.dumps(x))
        if not resp.ok:
            change_failed.append(
                {
                    "serialNumber": f"{x['interfaces'][0]['serialNumber']}",
                    "interface": f"{x['interfaces'][0]['nvPairs']['INTF_NAME']}",
                }
            )
        deploy_data.append(
            {
                "serialNumber": f"{x['interfaces'][0]['serialNumber']}",
                "ifName": f"{x['interfaces'][0]['nvPairs']['INTF_NAME']}",
                "fabricName": f"{sess.fabric}",
            }
        )
    if len(deploy_data) > 0:
        deploy = sess.post(dep_url, json.dumps(deploy_data))
        if deploy.ok:
            return True, change_failed
        else:
            return False, change_failed
    else:
        return (
            "\n\nInterface Descriptions already exist on all provided interfaces\n\n",
            change_failed,
        )


def main():
    """ main function is the logic of the script, it will call
    other functions and keep track of the dcnm session. (login/logout)
    """
    sess = get_connection()
    # jira_sess = jira_get_connection()
    # call class to use csv provided to get data back in correct format.
    data = DeploymentTracker.new(sess, from_csv=sys.argv[1], interfaces=True)
    # pass the list of dictionarys 'data.interfaces' to change_int_policy to do the work.
    # jira_create_ticket(connection_obj, summary, priority, description, label, component)
    # create_ticket = jira_create_ticket(jira_sess, f"DCNM Bulk Interface Description Update on {sess.fabric}", "Low", f"Change made via {sess.base_url}\n{{code}}{data.interfaces}{{code}}", "DCNM_Automation", "Fabric Migrations")
    # print(create_ticket)
    get_policy_info, no_work_needed = get_ints(sess, data.interfaces)
    if len(no_work_needed) > 0:
        print("Existing Description on:\n")
        print("\n".join(no_work_needed))
    result, failures = change_int_policy(sess, get_policy_info)
    if result == True:
        print("Successfully deployed interface description updates\n")
        # jira_update_ticket(jira_sess, create_ticket.split()[3], "Done", f"{jira_sess.user}", "Successfully deployed interface description updates")
        if len(failures) > 0:
            print(f"These failed:\n{','.join(failures)}")
    elif result == False:
        print("\nSomething failed, please login to DCNM GUI and verify\n")
        if len(failures) > 0:
            print(f"These failed:\n{','.join(failures)}")
    else:
        print(result)
    print(sess.logout())


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("csv", help="path to the csv file")
        parser.parse_args()
        if len(sys.argv) < 2:
            print(helpme)
            exit(1)
        main()
    except Exception as e:
        print(e)
