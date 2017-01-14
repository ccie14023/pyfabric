# pyfabric
Python script for provisioning Cisco campus fabric
=======

This script takes configuration parameters specified in a YAML file and builds a Cisco campus fabric edge node using NETCONF.

>  Note:  This is a very simple script and does not have error-checking.  It is a work-in-progress and I'm not a Python expert but it works!  Currently this works only with 16.3.2 YANG models.

I recommend using a virtualenvironment so you do not cause problems with existing libraries.

# Install
```
git clone https://github.com/ccie14023/pyfabric
pip install -r requirements.txt
```

# YAML file format
See fabric.yml for an example file format.  Note that vrfs takes a list of VRFs for the fabric, and under each VRF a pools list has the one or more IP address pools.

# Things to do
-  Add border capability
-  Add ability to specify devices and credentials in YAML file
-  Add error checking
-  Add command line options