#!/usr/bin/env python3
"""

python3 script

Program will take in a CSV with subnet, vlan and create the networks.

CSV Format:
subnet,vlan
192.168.5.0/24,995
192.168.6.0/24,996
192.168.7.0/24,997

Note: It is understood that this be used for initial network creations, interface attachments
        should be done using script <dcnm_bulk_network_overlay_attach.py>.

To Run:
    $ python dcnm_bulk_create.py <path to csv file>

    Todo:
        * todo
"""
import json, sys, os, signal, argparse
from pprint import pprint

try:
    from dcnm.core.dcnm_parsers import DeploymentTracker
    from dcnm.core.dcnm_calls import (
        get_connection,
        create_networks,
        attach_networks,
        deploy_networks,
        preview,
        bulk_create_networks,
    )

    # from dcnm.jira.jira_calls import jira_get_connection, jira_create_ticket, jira_update_ticket
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://github.com/alraytse/My-DCNM-Project.git"
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
    python3 dcnm_bulk_create_deploy.py data.csv

requires:
    python3
"""


def main():
    """ Main function acts as a 'full flow' function. It manages connection to DCNM takes in parsed csv
        data from DeploymentTrack.new() and creates all the networks in DCNM.  It next pulls all the
        leafs SerialNumbers and deploys that network to all LEAFs.
    """
    sess = get_connection()
    # jira_sess = jira_get_connection()
    deployment = DeploymentTracker.new(sess, from_csv=sys.argv[1])
    # How to Use jira_create_ticket(connection_obj, summary, priority, description, label, component)
    # create_ticket = jira_create_ticket(jira_sess, f"DCNM Bulk Network Add on {sess.fabric}", "Low", f"Change made via {sess.base_url}\n", "DCNM_Automation", "Fabric Migrations")
    # print(create_ticket)
    # jira_update_ticket(jira_sess, create_ticket.split()[3], "In Progress", f"{jira_sess.user}", f"Create Network Script Starting")
    create_result = bulk_create_networks(sess, sess.fabric, deployment.networks)
    print(create_result)
    print(f"Number of Networks to Create:{len(deployment.networks)}")
    if "successful" in create_result:
        print(
            f"Successfully Created: {len(list(x['name'] for x in create_result['successful']))}"
        )
    if "failed" in create_result:
        print(
            f"Failed to Created: {len(list(x['name'] for x in create_result['failed']))}"
        )
    if len(list(x["networkName"] for x in create_result["duplicates"])) > 0:
        print(
            f"Already Exist Didnt Create: {len(list(x['networkName'] for x in create_result['duplicates']))}\nNames:\n{', '.join(list(x['networkName'] for x in create_result['duplicates']))}\n"
        )
    # jira_update_ticket(connection_obj, ticket_name, desired_state, assignee, comment)
    # ticket_update = jira_update_ticket(jira_sess, create_ticket.split()[3], "Done", f"{jira_sess.user}", create_result)
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
