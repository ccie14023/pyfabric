#  Configures a campus fabric edge node from parameters specified in fabric.yml
#  Currently switch and login hard coded

import jinja2
import yaml
from ncclient import manager
import netaddr
import sys

CONFIG_FILE = "fabric.yml"
BASE_INSTANCE_ID = 10
USERNAME = 'admin'
PASSWORD = 'cisco123'
HOST = '172.26.244.61'

def load_yaml(filename):

	"""
		This file loads a dictionary from the YAML config file.  
		It returns the dictionary structured exactly as found in the file.
	"""

	y_file = open(filename,"r")

	params = yaml.load(y_file.read(),Loader=yaml.BaseLoader)

	y_file.close()

	return params

def build_lisp_mobility_strings(params):

	"""
	LISP requires mobility domain strings be configured per pool.  To make them unique
	we generate them by adding the IP address (with underscores instead of dots) to the
	VRF name.  IOS-XE returns an error if this is longer than 20 characters, so we truncate
	the string as needed.
	"""

	lm = {}

	for vrf in params['vrfs']:
		for pool in vrf['pools']:
			lm_name = vrf['name'][:abs(20 - (len(pool['addr']) + 4))]
			pool['lmd'] = lm_name + "_" + pool['addr'].replace('.','_')

	return params

def build_instance_ids(params):

	in_id = BASE_INSTANCE_ID

	for vrf in params['vrfs']:
		vrf['id'] = in_id
		in_id += 1

	return params

def render_xml(params, template_file):

	xml_file = open(template_file,"r")
	xml_template = xml_file.read()
	xml_file.close()

	t = jinja2.Template(xml_template, trim_blocks=True, lstrip_blocks=True)

	return t.render(params=params)

def send_nc(xml_string):

	"""
	Sends configuration to the device.  Takes a raw XML string and adds
	NC headers before sending.
	"""

	snippet = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><native xmlns="http://cisco.com/ns/yang/ned/ios">"""
	snippet = snippet + xml_string + "</native></config>"

	with manager.connect(host=HOST, port=830, username=USERNAME,password=PASSWORD) as m:
		assert(":validate" in m.server_capabilities)
		m.edit_config(target='running', config=snippet,
	    	test_option='test-then-set',error_option=None)	


if __name__ == "__main__":

	fabric_conf = load_yaml(CONFIG_FILE)  #  load base params from YAML config
	fabric_conf = build_instance_ids(fabric_conf)  #  add instance id's to each VRF
	#  YAML loader reads integers as unicode.  Next two lines correct the range values so we can iterate.
	fabric_conf['host-ifs']['min'] = int(fabric_conf['host-ifs']['min'])
	fabric_conf['host-ifs']['max'] = int(fabric_conf['host-ifs']['max'])
	#  Some config requires full mask, some CIDR.  Peel mask off address and add long notation mask to dict
	#  Also add VLAN id for each pool
	vlan_id = int(fabric_conf['base_vlan'])
	for vrf in fabric_conf['vrfs']:
		for pool in vrf['pools']:
			pool['mask'] = str(netaddr.IPNetwork(pool['subnet']).netmask)
			pool['addr'] = pool['subnet'][:-3]
			pool['vlan_id'] = str(vlan_id)
			vlan_id += 1

	fabric_conf = build_lisp_mobility_strings(fabric_conf)  #  add mobility strings to each pool


	send_nc(render_xml(fabric_conf, "vrf.xml"))  #  Send basic VRF config
	send_nc(render_xml(fabric_conf["host-ifs"], "interface.xml")) # Send host-facing interface config
	send_nc(render_xml(fabric_conf, "lisp.xml")) # Send LISP config
	send_nc(render_xml(fabric_conf,"vlan.xml")) # Send VLAN config

