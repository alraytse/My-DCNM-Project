# New Fabric Install DCNM API Scripts
************************
<br/><br/> 

**A collection of Python scripts related to DCNM through its API**

These scripts are useful when deploying NEW fabrics.  They can be used to change
all Access Leaf Ethernet1/1-48 port to policy "access_host" and also can be used
to add interface descriptions to interfaces in a bulk fashion.

**Order of task during a new fabric build is important.**

These scripts are assuming certain task were completed before they're ran.
1. Build Fabric, add freeform, s/w versions correct, POAP completed.
2. Run dcnm_interface_policy.py to change all access leaf Ethernet1/1-48 to access_host.
3. Run dcnm_interface_detail.py to add interface description to all ports.
4. Run dcnm_bulk_create_deploy.py to create networks.
5. Run dcnm_bulk_interface_attach.py to deploy/attach overlay networks to ports.

<br/><br/> 

* _*Scripts*_

For more advanced details please go into the file and read the doc-strings.

1. dcnm_interface_policy.py
>It will automatically change Ethernet1/1-48 on all ACCESS LEAFs from trunk_host
>to access_host policy assuming they have NO interface description.
>*Important Note: This will overwrite a trunk that has no interface description so
>this script should typically be a 'one time' use right after a fabric is built.

<br/><br/> 

### Contributors
******************

name | email
---|---
**Jeff Kala** | *jeff.kala@schwab.com*
**Jose Lima** | *jose.lima@schwab.com*
<br/><br/> 


[CSV_FORMAT_README]: https://bitbucket.schwab.com/projects/ENS/repos/dcnm_scripts/browse/production/CSV_FORMAT_README.md