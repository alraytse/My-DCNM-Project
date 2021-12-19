#!/usr/bin/env python3
"""

python3 script

Program will take in a CSV formated:
subnet,vlan,switch,ports
192.168.5.0/24,995,rlf02lab,"Port-channel100"
192.168.5.0/24,995,rlf03lab,"Port-channel100"

Note: This is used to backout of script <dcnm_bulk_network_overlay_attach.py>.

To Run:
    $ python dcnm_bulk_network_overlay_attach_backout.py <path to csv file>

    Todo:
    *Continue to tune the unexpected_commands list to ensure preview checking is as accurate as possible.
"""
import json, sys, os, signal, argparse
from pprint import pprint

try:
    from dcnm.core.dcnm_parsers import DeploymentTracker
    from dcnm.core.dcnm_calls import (
        get_connection,
        deploy_networks,
        deattach_interfaces,
        preview_fabric,
    )

    # from dcnm.jira.jira_calls import jira_get_connection, jira_create_ticket, jira_update_ticket
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://bitbucket.com/scm/ens/dcnm_core.git"
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
    python3 dcnm_bulk_network_overlay_attach_backout.py <path to data.csv>

requires:
    python3
    csv file in the correct format.
"""


def main():
    """ This program will be used to un-attach the overlay network from ports provided in the csv file.
        It will automatically do a preview and insure the unexpected_commands are not seen in the config to
        be pushed.
    """
    sess = get_connection()
    # jira_sess = jira_get_connection()
    deployment = DeploymentTracker.new(sess, from_csv=sys.argv[1], attach_info=True)
    # jira_create_ticket(connection_obj, summary, priority, description, label, component)
    # create_ticket = jira_create_ticket(jira_sess, f"DCNM Bulk Interface Attach BACKOUT on {sess.fabric}", "Low", f"Backout made via {sess.base_url}\n", "DCNM_Automation", "Fabric Migrations")
    # print(create_ticket)
    # jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", f"De-attaching Interfaces Script Starting")
    result = deattach_interfaces(sess, sess.fabric, deployment.networks)
    if result is True:
        # ticket_update = jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", "De-Attaching to interfaces was successful, un-deployment will happen next")
        preview_changes = preview_fabric(sess, sess.fabric)
        unexpected_commands = ["vlan add"]
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
        deploy = input('\n\nTo un-deploy\nType "Yes" or "No":\n').lower()
        if "y" in deploy:
            deploy_result = deploy_networks(
                sess, sess.fabric, list(x["networkName"] for x in deployment.networks)
            )
            if deploy_result is True:
                print(
                    "Interfaces were successfully de-attached from switches\n\n####\nMAKE SURE YOU GO INTO THE DCNM GUI AND VERIFY\n####\n"
                )
                # jira_update_ticket(jira_sess, create_ticket.split()[3], "Done", f"{jira_sess.user}", "Interfaces were successfully de-attached from switches")
        else:
            print("Exiting without un-attaching interfaces")
            sys.exit(0)
    else:
        print("Network Interface Unattachments Failed")
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
