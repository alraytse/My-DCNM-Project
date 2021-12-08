# *CSV file must contain headers and saved as MS-DOS CSV format in Excel!*

### **Adding Interface Descriptions to any number of ports on any switches.**

csv example:

```
device,interface,description
rlf02lab,Ethernet1/1,Test_Description
rlf14lab,Port-channel500,vPC_Description

```

### **Network creation/deployment/attach**

csv example:

```
network,vlan
10.0.0.0/24,222
10.0.10.0/24,333
10.0.20.0/24,444

```

### **Interface Attach/deployment/attach**

# *As of 11.3(1) you cannot attach borderleaf port at the same time as regular leaf ports. Must make 2 csvs.*

```
network,vlan,switch,interfaces
10.0.0.0/24,222,rlfe02bdc,"Ethernet1/10,Port-channel10"
10.0.10.0/24,333,rlfe02bdc,"Ethernet1/10,Port-channel10"
10.0.20.0/24,444,rlfe02bdc,"Ethernet1/10,Port-channel10"

```

Note:
  The 4th column has a list of interfaces comma separated in the same field.
  Please make sure all interfaces are in the same field inside of excel. CSV
  will wrap them in quotes e.g. "Ethernet1/10,Port-channel10", we take care of splitting
  them in the scripts. Also use proper case in the names DCNM is case sensitive.

  Invalid:
    ethernet1/10, port-Channel10

  Valid:
    Ethernet1/10, Port-channel10


### **Detach/undeploy**

The same files can be used to detach undeploy networks and interfaces, just use
the provided script to backout.


