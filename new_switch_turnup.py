#!/usr/bin/env python3
"""

python3 script

This program will POAP new ToR switches, add vPC peer between them, add all the schwab specific templates.

Note: It is understood that the new switches are visible in the POAP disovery before proceeding.

To Run:
    $ python new_switch_turnup.py

"""
import json, sys, os, signal, threading, time, urllib, yaml
from pprint import pprint
from getpass import getpass

try:
    from dcnm.core.dcnm_calls import *
except ImportError:
    print("\nmissing dcnm core module, please install first:\n")
    print(
        "python3 -m pip install git+https://bitbucket.schwab.com/scm/ens/dcnm_core.git"
    )
    exit(1)


def sigint_handler(signum, frame):
    print("...CTRL-C caught, aborting...")
    exit(1)


# catch ctrl-c to break any loops if needed
signal.signal(signal.SIGINT, sigint_handler)


class PoapSwitchObject:
    """

        This class will be used to track each switch that is being POAP'd it will be an object to be able
        to easily access specific attributes of the switch.

        Attributes:
            self.api_session = (obj) from the get_connection()
            self.switch_poap_info = (list of dict) This is a list of dictionaries from the GET poap API.
            self.serial_number = (str) switch serial number
            self.hostname = (str) switch hostname
            self.mgmt_ip = (str) switch mgmt IP address
            self.admin = (str) admin password used during POAP process.
            self.snmpuser = (str) snmpv3 username
            self.snmpauth = (str) auth password for snmpv3 user
            self.snmppriv = (str) priv password for snmpv3 use
            self.discovery_account = (str) tms svc account used by DCNM for discovery.
            self.discovery_p = (str) tms svc account password used by DCNM for discovery.
            self.tacacs_secret = (str) tacacs secret.

    """

    def __init__(self, api_session, switch_poap_info, input_data):
        self.api_session = api_session
        self.switch_poap_info = switch_poap_info
        self.serial_number = switch_poap_info[0]["serialNumber"]
        self.hostname = switch_poap_info[0]["hostname"]
        self.mgmt_ip = switch_poap_info[0]["ipAddress"]
        self.admin = input_data["admin_p"]
        self.snmpuser = input_data["snmpv3_u"]
        self.snmpauth = input_data["snmpv3_auth"]
        self.snmppriv = input_data["snmpv3_priv"]
        self.discovery_account = input_data["discovery_svc_account"]
        self.discovery_p = input_data["discovery_svc_p"]
        self.tacacs_secret = input_data["tacacs_secret"]

    def poap(self):
        """
        This submit the POST for the POAP definition.  Once this call is made a refresh of the GUI
        will show the new switches in fabric builder.
        """
        resp = poap_submit(
            self.api_session, self.api_session.fabric, self.switch_poap_info
        )
        if resp == True:
            print("Successfully submitted POAP Definition")
        else:
            print("Something failed with the POAP Definition Submission")

    def feature_tacacs(self):
        """
        Will add the tacacs feature template/policy to the switch with
        priority of 50.

        returns:
            (json) - json object with the information needed for the template POST call.
        """
        return json.dumps(
            {
                "source": "",
                "serialNumber": f"{self.serial_number}",
                "entityType": "SWITCH",
                "entityName": "SWITCH",
                "templateName": "feature_tacacs",
                "priority": "50",
                "nvPairs": {},
            }
        )

    def schwab_go_live(self):
        """
        Will add the schwab_go_live template/policy to the switch with priority 490.
        It will ask for input on whether you want AAA Authorize turned on and the same for logging.

        returns:
            (json) - json object with the information needed for the template POST call.
        """
        aaa_authorize = input("Turn AAA Authorization on?\ntrue or false\n").lower()
        print(f"Enter information for {self.hostname}\n")
        if "t" in aaa_authorize:
            aaa_authorize = True
        elif "f" in aaa_authorize:
            aaa_authorize = False
        logging = input("Turn on Logging?\ntrue or false\n").lower()
        if "t" in logging:
            logging = True
        elif "f" in logging:
            logging = False
        if "PDC1-LAB-Fabric" in self.api_session.fabric:
            # come back and update location to a input option
            template_data = json.dumps(
                {
                    "source": "",
                    "serialNumber": f"{self.serial_number}",
                    "entityType": "SWITCH",
                    "entityName": "SWITCH",
                    "templateName": "schwab_go_live",
                    "priority": "490",
                    "nvPairs": {
                        "ROLE": "READONLY",
                        "CONTACT": "NOCC 1-877-977-5789 X2",
                        "LOCATION": self.api_session.fabric,
                        "AAA_AUTH_ENABLE": aaa_authorize,
                        "LOGGING_ENABLE": logging,
                        "TIME_ENABLE": True,
                        "TACACS_SERVER_1": "10.101.136.127",
                        "TACACS_SERVER_2": "",
                        "TACACS_SERVER_3": "",
                        "TACACS_SERVER_4": "",
                        "TACACS_SECRET": f"{self.tacacs_secret}",
                        "LOGGING_SERVER_1": "",
                        "LOGGING_SERVER_2": "",
                        "LOGGING_SERVER_3": "",
                        "NTP_PREFER": "10.253.16.209",
                    },
                }
            )
            return template_data
        else:
            template_data = json.dumps(
                {
                    "source": "",
                    "serialNumber": f"{self.serial_number}",
                    "entityType": "SWITCH",
                    "entityName": "SWITCH",
                    "templateName": "schwab_go_live_priority_490_V2",
                    "priority": "490",
                    "nvPairs": {
                        "ROLE": "READONLY",
                        "CONTACT": "NOCC 1-877-977-5789 X2",
                        "LOCATION": self.api_session.fabric,
                        "AAA_AUTH_ENABLE": aaa_authorize,
                        "LOGGING_ENABLE": logging,
                        "TIME_ENABLE": True,
                        "TACACS_SERVER_1": "10.253.190.1",
                        "TACACS_SERVER_2": "10.102.12.5",
                        "TACACS_SERVER_3": "10.192.17.149",
                        "TACACS_SECRET": f"{self.tacacs_secret}",
                        "LOGGING_SERVER_1": "10.100.180.18",
                        "LOGGING_SERVER_2": "10.104.180.18",
                        "LOGGING_SERVER_3": "10.253.77.195",
                        "NTP_PREFER": "10.253.76.23",
                    },
                }
            )
            return template_data

    def schwab_snmpv3_user_aes(self):
        """
        Will add the snmpv3 user with aes encryption
        priority of 500. Must be after the go live priority

        returns:
            (json) - json object with the information needed for the template POST call.
        """
        return json.dumps(
            {
                "source": "",
                "serialNumber": f"{self.serial_number}",
                "entityType": "SWITCH",
                "entityName": "SWITCH",
                "templateName": "Schwab_snmpv3_user_aes",
                "priority": "500",
                "nvPairs": {
                    "USERNAME": self.snmpuser,
                    "USER_ROLE": "READONLY",
                    "AUTH": self.snmpauth,
                    "PRIV": self.snmppriv,
                },
            }
        )

    def schwab_igmp_snooping(self):
        """
        Will add igmp snooping command to the switches.
        priority of 500.

        returns:
            (json) - json object with the information needed for the template POST call.
        """
        return json.dumps(
            {
                "source": "",
                "serialNumber": f"{self.serial_number}",
                "entityType": "SWITCH",
                "entityName": "SWITCH",
                "templateName": "Schwab IGMP Snooping",
                "priority": "500",
                "nvPairs": {"NONE": "None"},
            }
        )


def switch_information(poap_info, admin_password):
    """
    All details needed for initial device poap.
    poap_info example {'serialNumber': 'FDO22222T3N', 'model': 'N9K-C93108TC-FX', 'version': '7.0(3)I7(7)', 'data': '{"gateway": "10.128.18.254/24", "modulesModel": ["N9K-C93108TC-FX"]}'}
    example of

    returns:
        (list)
        [{'serialNumber': 'FDO22222T3N', 'model': 'N9K-C93108TC-FX', 'version': '7.0(3)I7(7)', 'data': '{"gateway": "10.128.18.254/24", "modulesModel": ["N9K-C93108TC-FX"]}', 'hostname': 'rlf14lab', 'ipAddress': '1.1.1.1', 'password': 'fake_passwd'}]
    """
    poap_info[0]["hostname"] = input("\nEnter Switch Hostname\n")
    poap_info[0]["ipAddress"] = input("\nEnter Switch Mgmt IP Address\n")
    poap_info[0]["password"] = admin_password
    return poap_info


def get_options(creds_dict=None):
    """
    Used to specify some credentials and parameters to avoid inputs and static entries.
    switch_turnup.key is a yaml file.  Please fill out the below information.

    ---
    admin_p:
    snmpv3_u:
    snmpv3_auth:
    snmpv3_priv:
    discovery_svc_account:
    discovery_svc_p:
    tacacs_secret: '<tacacs secrret with "">' #make sure single quotes are on the outside since the secret include "" around it.

    returns:
        (dict) of the keys above with their corresponding values, to be used in other functions/classes.
    """
    try:
        file = os.path.expanduser("~/switch_turnup.key")
        with open(file) as f:
            return yaml.safe_load(f)
    except Exception as e:
        pass


def main(creds_inputs):
    """
    main() will serve as the main program logic for the poap full flow automation.
    """
    # dcnm_calls which calls Session from session.py which creates an object.
    sess = get_connection()
    # This returns a list of devices that DCNM currently sees as "Poap-able".  If switches exist print s/n's else exit.
    get_poap_list = poap_device_list(sess, sess.fabric)
    if len(get_poap_list) > 0:
        print("Switches Available to POAP\n")
        for poap_def in get_poap_list:
            print(poap_def["serialNumber"])
    else:
        print("No switches are currently attempting to POAP\nProgram exiting.....\n")
        exit(1)
    # Create the switch definitions for both switches.
    sn_sw1 = input("Enter first Serial Number\n")
    sw1 = switch_information(
        [poap_def for poap_def in get_poap_list if poap_def["serialNumber"] == sn_sw1],
        creds_inputs["admin_p"],
    )
    sn_sw2 = input("Enter second Serial Number\n")
    sw2 = switch_information(
        [poap_def for poap_def in get_poap_list if poap_def["serialNumber"] == sn_sw2],
        creds_inputs["admin_p"],
    )
    # Instantiate class for both switches
    poap_sw1 = PoapSwitchObject(sess, sw1, creds_inputs)
    poap_sw2 = PoapSwitchObject(sess, sw2, creds_inputs)
    # Actually submit the poap definition to DCNM
    poap_sw1.poap()
    poap_sw2.poap()
    print("Switches are POAP'ing sleeping 7 minutes for switch reboots\n")
    for remaining in range(7, 0, -1):
        print(f"{remaining} Minutes Remaining on Sleep")
        time.sleep(60)
    sess.login()
    print("Attempting vPC peering setup\n")
    # Testing to renew auth should the reboot take longer than expected.
    vpc_ready = False
    while not vpc_ready:
        vpc_rec_resp = vpc_recommendation(sess, poap_sw1.serial_number)
        for sw in vpc_rec_resp:
            if sw["serialNumber"] == poap_sw2.serial_number:
                if (
                    sw["recommendationReason"]
                    == "Switches are connected and have same role"
                ):
                    vpc_ready = True
                    print(sw["recommendationReason"])
                    print("vPC recommendation successful\nvPC Config will be added")
                    vpc_peer_add = vpcpair(
                        sess, poap_sw1.serial_number, poap_sw2.serial_number
                    )
                    if vpc_peer_add == True:
                        print("VPC Pair created successfully\n")
                    else:
                        print("VPC Pair Un-successful\n")
                else:
                    print(sw["recommendationReason"])
                    print("vPC not Ready Sleeping 30 seconds....\n")
                    vpc_ready = False
                    time.sleep(30)
    sess.login()
    print("Adding Schwab Specific Templates\n")
    add_template(sess, poap_sw1.feature_tacacs())
    add_template(sess, poap_sw1.schwab_go_live())
    add_template(sess, poap_sw1.schwab_snmpv3_user_aes())
    add_template(sess, poap_sw1.schwab_igmp_snooping())
    add_template(sess, poap_sw2.feature_tacacs())
    add_template(sess, poap_sw2.schwab_go_live())
    add_template(sess, poap_sw2.schwab_snmpv3_user_aes())
    add_template(sess, poap_sw2.schwab_igmp_snooping())
    fab_save = fabric_config_save(sess, sess.fabric)
    if fab_save == True:
        print("Fabric Configs Saved\nDeployments will happen next....")
    print("Temporarily updating lan creds to admin user\n")
    sess.update_lan_creds(other_user="admin", other_passwd=poap_sw1.admin)
    # vpc pair so will automatically deploy to both switches.
    single_switch_deploy(sess, sess.fabric, poap_sw1.serial_number)
    # set lan creds back to a.d account
    sess.update_lan_creds()
    # update discovery creds from admin to svc account now that tacacs is on.
    discovery_details = discovery_info(sess)
    for entry in discovery_details:
        if (
            entry["serialNo"] == poap_sw1.serial_number
            or entry["serialNo"] == poap_sw2.serial_number
        ):
            info_to_encode = {
                "lanKeys": entry["lanId"],
                "seedIps": entry["seedSwIP"],
                "cdpSeedKeys": entry["csSeedDbId"],
                "cdpTaskTypes": entry["taskType"],
                "cdpSeedDbIds": entry["csSeedDbId"],
                "isV3": "true",
                "username": creds_inputs["discovery_svc_account"],
                "password": creds_inputs["discovery_svc_p"],
                "v3protocol": "0",
                "maxHops": "null",
                "groupDbIds": entry["groupDbId"],
                "serverIpaddress": entry["fmServerIPString"],
            }
            encoded_data = urllib.parse.urlencode(info_to_encode)
            sess.update_discovery_creds(encoded_data)
    # push spine configs
    fabric_config_save(sess, sess.fabric)
    inventory = get_inventory(sess, sess.fabric)
    spines_sns = [dev.split(",")[3] for dev in inventory if "rsp" in dev]
    threads = []
    for sn_deploy in range(len(spines_sns)):
        process = threading.Thread(
            target=single_switch_deploy, args=[sess, sess.fabric, spines_sns[sn_deploy]]
        )
        print(f"Config-deploy for {spines_sns[sn_deploy]}")
        process.start()
        threads.append(process)
    for process in threads:
        process.join()
    print("Everything was successful. Please verify in the GUI\n")
    logout = sess.logout()
    if logout.ok:
        print(f"API Logout Successful")


if __name__ == "__main__":
    try:
        creds = get_options()
        if not creds:
            creds = {
                "admin_p": input("Enter Admin Password for Switches:\n"),
                "snmpv3_u": input("Enter SNMPv3 Username:\n"),
                "tacacs_secret": input('Enter tacacs secret key including "":\n'),
                "snmpv3_auth": getpass("Enter SNMPv3 User Auth Password:\n"),
                "snmpv3_priv": getpass("Enter SNMPv3 User Priv Password:\n"),
                "discovery_svc_account": input(
                    "Enter Username for SVC Account for Discovery:\n"
                ),
                "discovery_svc_p": getpass(
                    "Enter Password for SVC Account for Discovery:\n"
                ),
            }
        main(creds)
    except Exception as e:
        print(e)
