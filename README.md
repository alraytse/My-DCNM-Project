# Production DCNM API Scripts
************************
<br/><br/> 

**A collection of Python scripts related to DCNM through its API**

These scripts are in productino, they've been fully tested.


<br/><br/> 

* _*Scripts*_

For more advanced details please go into the file and read the doc-strings.

1. dcnm_bulk_create.py
>Program will take in a CSV with subnet, vlan and create the networks.

2. dcnm_bulk_network_overlay_attach.py
>Takes in a CSV with subnet,vlan,device,ports and attaches the overlay to the ports.  If the network hasn't been configured on the switch it will also configure the vxlan_profile.

3. dcnm_bulk_network_overlay_attach_backout.py
>Does the opposite of the regular version.  This should only be run to backout of a failed change. It takes the same exact CSV file that was used to deploy the changes.

4. new_switch_turnup.py
>This program can automate the POAP and schwab template attach for a pair of new switches.  It does everything needed to bring up a new pair of leafs into the fabric.  It will.
    * POAP
    * Create VPC Peer
    * Attach all the Schwab Specific Templates
    * Update discovery credentials.

>All of the needed informatino should be in a file ~/switch_turnup.key.  Its a yaml file but doesn't need to be saved as a yaml file. Keep the .key extention.  Fill in the properties.
>NOTE: If the yaml file does NOT exist then you will just get propmpted for each of the necessary peices of data.

```
    ---
    admin_p: 
    snmpv3_u: 
    snmpv3_auth: 
    snmpv3_priv: 
    discovery_svc_account: 
    discovery_svc_p: 
    tacacs_secret: '<tacacs secrret with "">' #make sure single quotes are on the outside since the secret include "" around it.
```

5. utility_interface_desc_verify.py
>Can take in a CSV from the interface description bulk script and compare the CSV to what DCNM has.  This is a nice quick way to verify the interface description successfully deployed.

6. dcnm_bulk_interface_desc.py
>NOTE: Formally was called dcnm_interface_detail.py.  Will take in a CSV file and deploy interface descriptions in a bulk fashion.


<br/><br/> 

### Contributors
******************

n


[CSV_FORMAT_README]: https://bitbucket.schwab.com/projects/ENS/repos/dcnm_scripts/browse/production/CSV_FORMAT_README.md
