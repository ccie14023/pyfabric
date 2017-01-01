#  Configures a campus fabric edge node from parameters specified in fabric.yml
#  Currently switch and login hard coded

import jinja2
import yaml
from ncclient import manager

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

	lm = {}

	for vrf in params['vrfs']:
		for pool in vrf['pools']:
			pool['lmd'] = vrf['name'] + "_" + pool['subnet'].replace('.','_')

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

	t = jinja2.Template(xml_template)


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
	fabric_conf = build_lisp_mobility_strings(fabric_conf)  #  add mobility strings to each pool
	fabric_conf = build_instance_ids(fabric_conf)  #  add instance id's to each VRF

	send_nc(render_xml(fabric_conf, "vrf.xml"))  #  Send basic VRF config
	send_nc(render_xml(fabric_conf, "lisp.xml"))
