#  Configures campus fabric edge nodes from parameters defined in fabric.yml


import jinja2
import yaml
from ncclient import manager
import netaddr
import sys

CONFIG_FILE = "fabric.yml"
BASE_INSTANCE_ID = 10

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

	"""
	Adds instance IDs to the parameters.  These are required for LISP.
	Takes the parameters dictionary and returns a modified version of it.
	"""

	in_id = BASE_INSTANCE_ID

	for vrf in params['vrfs']:
		vrf['id'] = in_id
		in_id += 1

	return params

def render_xml(params, template_file):

	"""
	Takes the fabric config dictionary and any template file, and renders it.
	"""

	xml_file = open(template_file,"r")
	xml_template = xml_file.read()
	xml_file.close()

	t = jinja2.Template(xml_template, trim_blocks=True, lstrip_blocks=True)

	return t.render(params=params)

def send_nc(xml_string, switch, username, password):

	"""
	Sends configuration to the device.  Takes a raw XML string and adds
	NC headers before sending.
	"""

	head = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><native xmlns="http://cisco.com/ns/yang/ned/ios">"""
	tail = "</native></config>"

	snippet = '{}{}{}'.format(head, xml_string, tail)

	with manager.connect(host=switch, port=830, username=username,password=password) as m:
		assert(":validate" in m.server_capabilities)
		m.edit_config(target='running', config=snippet,
	    	test_option='test-then-set',error_option=None)	

def fixup_fabric_conf(config):
	
	#  YAML loader reads integers as unicode.  Next two lines correct the range values so we can iterate.
	config['host-ifs']['min'] = int(config['host-ifs']['min'])
	config['host-ifs']['max'] = int(config['host-ifs']['max'])
	#  Some config requires full mask, some CIDR.  Peel mask off address and add long notation mask to dict
	#  Also add VLAN id for each pool
	vlan_id = int(config['base_vlan'])
	for vrf in config['vrfs']:
		for pool in vrf['pools']:
			pool['mask'] = str(netaddr.IPNetwork(pool['subnet']).netmask)
			pool['addr'] = pool['subnet'][:-3]
			pool['vlan_id'] = str(vlan_id)
			vlan_id += 1

	return config

def main():

	# Load the config from the YAML file and clean it up/add some params
	fabric_conf = load_yaml(CONFIG_FILE)  #  load base params from YAML config
	fabric_conf = build_instance_ids(fabric_conf)  #  add instance id's to each VRF
	fabric_conf = fixup_fabric_conf(fabric_conf)  #  Convert unicode to ints and add full subnet masks
	fabric_conf = build_lisp_mobility_strings(fabric_conf)  #  add mobility strings to each pool

	
	for edge in fabric_conf['edges']:
		print "Configuring edge node with IP %s..." % edge['ip']
		#  Render and send the four main code blocks to the switch
		print "  Configuring VRFs..."
		send_nc(render_xml(fabric_conf, "vrf.xml"), switch=edge['ip'], username=edge['username'], password=edge['password'])  #  Send basic VRF config
		print "  Configuring interfaces..."
		send_nc(render_xml(fabric_conf["host-ifs"], "interface.xml"), switch=edge['ip'], username=edge['username'], password=edge['password']) # Send host-facing interface config
		print "  Configuring LISP..."
		send_nc(render_xml(fabric_conf, "lisp.xml"), switch=edge['ip'], username=edge['username'], password=edge['password']) # Send LISP config
		print "  Configuring VLANs and SVIs..."
		send_nc(render_xml(fabric_conf,"vlan.xml"), switch=edge['ip'], username=edge['username'], password=edge['password']) # Send VLAN config
	print "Configuration complete"


if __name__ == "__main__":

	main()

