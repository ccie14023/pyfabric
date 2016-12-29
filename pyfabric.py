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

def build_lisp_mobility_strings(pools):

	lm = {}

	for pool in pools:
		lm[pool['subnet']] = pool['vrf'] + '_' + pool['subnet'].replace('.','_')

	return lm

def build_pool_dict(params, lm):

	"""
		The YAML file allows you to list the pools in any order, regardless of VRF.  However,
		we can't pass this to the J2 template.  Therefore we will create a dictionary which
		has the pools listed in order of VRF.
	"""

	pool_dict = {}

	for vrf in params['vrfs']:
		pool_dict[vrf] = []

	for vrf in pool_dict:
		for pool in params['pools']:
			if pool['vrf'] == vrf:
			  new_pool = {k:v for k,v in pool.items()}  # copy the current pool to new dict
			  new_pool['lmd'] = lm[new_pool['subnet']]
			  pool_dict[vrf].append(new_pool)

	return pool_dict



def render_xml(params, ids):

	x_file = open("lisp.xml","r")
	xml_template = x_file.read()
	x_file.close()

	t = jinja2.Template(xml_template)

	vrf_list = zip(params['vrfs'],ids)
	print t.render(border_ip = params['border'], vrf_list=vrf_list)


if __name__ == "__main__":

	params = load_yaml(CONFIG_FILE)
	
	# Build instance ID list based on VRFs defined in YAML file
	instance_ids = []
	instance_id = BASE_INSTANCE_ID
	for vrf in params['vrfs']:
		instance_ids.append(instance_id)
		instance_id += 1

	lm = build_lisp_mobility_strings(params['pools'])

	pools = build_pool_dict(params,lm)

	print render_xml(params, instance_ids)
