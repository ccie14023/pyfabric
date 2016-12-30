#  Configures a campus fabric edge node from parameters specified in fabric.yml
#  Currently switch and login hard coded

import jinja2
import yaml
from ncclient import manager

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

def render_xml(params):

	x_file = open("lisp.xml","r")
	xml_template = x_file.read()
	x_file.close()

	t = jinja2.Template(xml_template)

	return t.render(border_ip = params['border'], vrf_list=params['vrfs'])

def send_nc(xml_string):

	xml_data = """<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"><native xmlns="http://cisco.com/ns/yang/ned/ios">"""
	xml_data = xml_data + xml_string + "</native></config>"

	print xml_data


if __name__ == "__main__":

	params = load_yaml(CONFIG_FILE)  #  load base params from YAML config
	params = build_lisp_mobility_strings(params)  #  add mobility strings to each pool
	params = build_instance_ids(params)  #  add instance id's to each VRF

	send_nc(render_xml(params))
