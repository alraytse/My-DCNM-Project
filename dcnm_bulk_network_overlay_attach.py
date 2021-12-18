#!/usr/bin/env python3
"""

python3 script

Program will take in a CSV formated:
subnet,vlan,switch,ports
192.168.5.0/24,995,rlf02lab,"Port-channel100,Ethernet1/1"
192.168.5.0/24,995,rlf03lab,"Port-channel100,Ethernet1/1"

Note: It is understood that this be used AFTER running the inital network create script. <dcnm_bulk_create.py>

To Run:
    $ python dcnm_bulk_network_overlay_attach.py <path to csv file>

    Todo:
    *Continue to tune the unexpected_commands list to ensure preview checking is as accurate as possible.
"""
import sys, os, json, signal, argparse
from pprint import pprint

try:
    from dcnm.core.dcnm_parsers import DeploymentTracker
    from dcnm.core.dcnm_calls import (
        get_connection,
        attach_networks,
        deploy_networks,
        preview_fabric,
    )

    # from dcnm.jira.jira_calls import jira_get_connection, jira_create_ticket, jira_update_ticket
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://bitbucket.dcnm_core.git"
    )
    exit(1)


def sigint_handler(signum, frame):
    print("...CTRL-C caught, aborting...")
    exit(1)


# catch ctrl-c to break any loops if needed
signal.signal(signal.SIGINT, sigint_handler)

helpme = """
Please provide a CSV file including CSV headers, pass the file as an argument to this script

run:
    python3 dcnm_bulk_network_overlay_attach.py data.csv

requires:
    python3
    csv file in the proper format.
"""


def main():
    """ This program will be used to deploy a network to a switch, and also attach overlay network to ports
        provided in the csv file.  If the network is already on the switch it knows to only do the overlay
        port attach.  If neither exist it will do both.
        It will automatically do a preview and insure the unexpected_commands are not seen in the config to
        be pushed.
    """
    sess = get_connection()
    # jira_sess = jira_get_connection()
    deployment = DeploymentTracker.new(sess, from_csv=sys.argv[1], attach_info=True)
    # Example of deployment.networks:  [{'networkName': 'TEST_API_1','vlanId':999, 'attachInfo': [{'serialNumber': FDO220324GK','interfaces': 'Port-channel100,Port-channel110'},{'serialNumber': FDO22112VQU','interfaces': 'Port-channel100,Port-channel110'}'']}]
    # How to Use jira_create_ticket(connection_obj, summary, priority, description, label, component)
    # create_ticket = jira_create_ticket(jira_sess, f"DCNM Bulk Interface Attach on {sess.fabric}", "Low", f"Change made via {sess.base_url}\n", "DCNM_Automation", "Fabric Migrations")
    # print(create_ticket)
    # jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", f"Interface Attach Script Starting")
    result = attach_networks(sess, sess.fabric, deployment.networks)
    if result is True:
        # ticket_update = jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", "Attaching to interfaces was successful, deployment will happen next")
        unexpected_commands = ["no vni", "no apply profile", "no vlan", "vlan remove"]
        preview_changes = preview_fabric(sess, sess.fabric)
        print(
            "Checking to see if any of these unexpected commands are in the preview:",
            *unexpected_commands,
            sep=", ",
        )
        for sw in preview_changes:
            if sw["status"] == "OUT_OF_SYNCH":
                print(sw["switchName"], sw["status"])
                for info in sw["entityList"]:
                    bad_commands = list(
                        command
                        for command in info["commands"]
                        for unexpected in unexpected_commands
                        if unexpected in command
                    )
                    if len(bad_commands) > 0:
                        print(
                            "The following commands are unexpected for a network attach or port attach\nPlease verify!\n",
                            *bad_commands,
                            sep="\n",
                        )
                    else:
                        print("Config Preview Command Validation Passed\n")
        deploy = input('\n\nTo deploy\nType "Yes" or "No":\n').lower()
        if "y" in deploy:
            deploy_result = deploy_networks(
                sess, sess.fabric, list(x["networkName"] for x in deployment.networks)
            )
            if deploy_result is True:
                print(
                    "Interfaces were successfully attached\n\n####\nMAKE SURE YOU GO INTO THE DCNM GUI AND VERIFY\n####\n\n"
                )
                # jira_update_ticket(jira_sess, create_ticket.split()[3], "Done", f"{jira_sess.user}", "Interfaces were successfully attached")
        else:
            print("Exiting Without Deploying Interfaces")
            sys.exit(0)
    else:
        print("Network Interface Attachments Failed")
        sys.exit(0)
    logout = sess.logout()
    if logout.ok:
        print(f"API Logout Successful")


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
