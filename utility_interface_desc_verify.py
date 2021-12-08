#!/usr/bin/env python
"""Used to verify after running dcnm_bulk_interface_desc.py


4/29/2019

Used for a post check after adding interface descriptions.

Csv Format
device,interface,description

TODO:

"""
import json
import sys
import argparse
from getpass import getpass
from pprint import pprint
from dcnm.core.dcnm_calls import get_connection
from dcnm.core.dcnm_parsers import DeploymentTracker


def api_call(connection, rest_call):
    """ simple call to get results from a endpoint
    args:
        connection (obj) - handles connection to dcnm.
        rest_call (str) - api endpoint example /rest/inventory/switches'
    return:
        data from the api call
    """
    return connection.get(rest_call)


def main():
    """ main function is the logic of the script, it will call
    other functions and keep track of the dcnm session. (login/logout)
    """
    connection = get_connection()
    deployment = DeploymentTracker.new(
        connection, from_csv=sys.argv[1], interfaces=True
    )
    # print(deployment.interfaces)
    url = "/rest/interface/detail"
    data = api_call(connection, url)
    data = json.loads(data.text)
    for interface in deployment.interfaces:
        for entry in data:
            if (
                entry["sysName"] == interface["deviceName"]
                and entry["ifName"] == interface["ifName"]
            ):
                if entry["alias"] == interface["DESC"]:
                    print(
                        f'CSV and DCNM Match for {interface["deviceName"]} {interface["ifName"]}'
                    )
                else:
                    print(
                        f'Mismatch between CSV and DCNM on {interface["deviceName"]} {interface["ifName"]} CSV:{interface["DESC"]} DCNM:{entry["alias"]}'
                    )
    connection.logout()


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
