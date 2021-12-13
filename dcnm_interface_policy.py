#!/usr/bin/env python3
"""

python3 script

Will be used to bulk update interface policies after fabric deploy.

NOTE: 
*It will automatically change Ethernet1/1-48 on all ACCESS LEAFs from trunk_host to access_host policy assuming they have NO interface description.
If a trunk already has a description on it, this script will pass on that interface and leave it as is.

*If ports are already access_host it does NOTHING to them.

*If a trunk has an overlay attached with NO interface description it maybe cause dcnm to go into an inconstant state.
TODO:
*Add functionality to check if overlay is attached and skip interface.
"""
import json, sys, re, time
from pprint import pprint

try:
    from dcnm.core.session import Session
    from dcnm.core.dcnm_calls import get_connection, get_inventory
    from dcnm.core.dcnm_parsers import DeploymentTracker

    # from dcnm.jira.jira_calls import jira_get_connection, jira_create_ticket, jira_update_ticket
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://https://github.com/alraytse/DCNM_Core.git"
    )
    exit(1)


def get_ints(sess, access_leafs):
    """ Function used to identify any ports Ethernet1/1 - 48 that have interface policy trunk_host
        on each Access leaf and check if a descripton on the port exist, if a trunk_host has a 
        description it will NOT add it to the update_list.  It will only add trunk_host that have 
        no descriptions.  It is assumed trunk_host with no description should be changed to access_host.

    Args:   sess (obj) - is imported from main and is keeping track of the session connection to DCNM.
            access_leafs (list) of serial numbers

    returns:
            final_dict (dict) this dictionary has the key = serial number, and values = to (list) of interfaces
                              that need to be changed to access_host.
    """
    final_dict = {}
    # Regex to find Ethernet1/1 - 48 ONLY if it's Ethernet1/49+ it won't be anaylzed.
    regex = r"\bEthernet1/([1-9]|[1-3][0-9]|4[0-8])\b"
    for x in access_leafs:
        """ For each access_leaf pull all the interfaces from Eth1/1-48 and check for a description
            if a description exist PASS, else add it to update_list.  Finally once all ports for each
            switch are analyzed add the update_list to be the value of k,v (serial_number : [interfaces])
        """
        update_list = []
        get_url = f"/rest/interface?serialNumber={x}"
        resp = sess.get(get_url)
        data = json.loads(resp.text)
        if resp.ok:
            for policy_type in data:
                if "trunk_host" in policy_type["policy"]:
                    for interface in policy_type["interfaces"]:
                        if len(interface["nvPairs"]["DESC"]) == 0:
                            if (
                                bool(
                                    re.search(regex, interface["nvPairs"]["INTF_NAME"])
                                )
                                == True
                            ):
                                update_list.append(interface["nvPairs"]["INTF_NAME"])
                            else:
                                print(
                                    f"interface failed regex {interface['nvPairs']['INTF_NAME']}"
                                )
                        else:
                            print(
                                f"Interface Description Exist not changing to default interface {x}:{interface['nvPairs']['INTF_NAME']}"
                            )
            if len(update_list) > 0:
                final_dict[f"{x}"] = update_list
    return final_dict


def change_int_policy(sess, change_data):
    """ Function used to actually change the interface policy based on the interfaces provided from
        get_ints().  It will then attach followed by Deploy the changes.
    
    Args:   sess (obj) - is imported from main and is keeping track of the session connection to DCNM.
            change_data (dictionary) of serial numbers

    returns:
            Boolean True for success or False for failed.
    """
    change_url = "/rest/interface"
    # note gloablInterface appears to be the same as interface possibly changed from 10.4(2) to 11.0(1) need to test
    # /rest/interface/deploy before pushing changing.  Meantime it works on both version as is.
    deploy_url = "/rest/globalInterface/deploy"
    final_data = []
    deploy_data = []
    for sn in change_data.keys():
        # This section of code simply makes the json payload that will become the body of the HTTP post.
        for interface in change_data[f"{sn}"]:
            final_data.append(
                {
                    "serialNumber": f"{sn}",
                    "interfaceType": "INTERFACE_ETHERNET",
                    "ifName": f"{interface}",
                    "fabricName": f"{sess.fabric}",
                    "nvPairs": {
                        "BPDUGUARD_ENABLED": True,
                        "ADMIN_STATE": True,
                        "DESC": "",
                        "INTF_NAME": f"{interface}",
                        "PORTTYPE_FAST_ENABLED": True,
                        "MTU": "jumbo",
                    },
                }
            )
            deploy_data.append(
                {
                    "serialNumber": f"{sn}",
                    "ifName": f"{interface}",
                    "fabricName": f"{sess.fabric}",
                }
            )
    dict_values = {"policy": "access_host", "interfaces": final_data}
    pprint(dict_values)
    resp = sess.put(change_url, json.dumps(dict_values))
    if resp.ok:
        print("Deploying Now....\n")
        resp1 = sess.post(deploy_url, json.dumps(deploy_data))
        if resp1.ok:
            return True
        else:
            return False


def access_leaf_dict(inv):
    """Will pull inventory and look for any access leaf C93108 or C93180
    then pass it to change_int_policy

    Args:
        inv (list) - list returned from get_inventory function call.
    
    return:
        list of Serial Numbers to change.
    """
    inv_dict = {}
    for device in inv:
        device = device.split(",")
        if "C93108" in device[6]:
            inv_dict[device[0]] = device[3]
        elif "C93180" in device[6]:
            inv_dict[device[0]] = device[3]
    print([x[0] for x in inv_dict.items()])
    answer = input(
        "\n\nChange Eth1/1-48 to access policy on all Access Leafs? Type yes\n\nif you want only certain switches enter the device hostname from list above and hit enter, comma seperate for multiple:\n"
    ).lower()
    if "yes" in answer:
        return [inv_dict[devs] for devs in inv_dict]
    else:
        return [inv_dict[devs] for devs in answer.split(",")]


def main():
    """ main function is the logic of the script, it will call
    other functions and keep track of the dcnm session. (login/logout)
    """
    sess = get_connection()
    # jira_sess = jira_get_connection()
    inventory = get_inventory(sess, sess.fabric)
    # jira_create_ticket(connection_obj, summary, priority, description, label, component)
    # create_ticket = jira_create_ticket(jira_sess, f"DCNM Bulk Interface Policy Update on {sess.fabric}", "Low", f"Change made via {sess.base_url}", "DCNM_Automation", "Fabric Migrations")
    # print(create_ticket)
    al_list = access_leaf_dict(inventory)
    ints_to_change = get_ints(sess, al_list)
    # jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", ints_to_change)
    result = change_int_policy(sess, ints_to_change)
    if result == True:
        print("Successfully deployed interface policy change\n")
        # jira_update_ticket(jira_sess, create_ticket.split()[3], "Done", f"{jira_sess.user}", "Successfully deployed interface policy change")
    else:
        print("\nSomething failed, please login to DCNM GUI and verify\n").upper()
    print(sess.logout())


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
