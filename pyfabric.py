#  Configures a campus fabric edge node from parameters specified in fabric.yml
#  Currently switch and login hard coded

import jinja2
import yaml
from ncclient import manager

CONFIG_FILE = "fabric.yml"

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

def render_xml(params):

	x_file = open("lisp.xml","r")
	xml_template = x_file.read()
	x_file.close()

	t = jinja2.Template(xml_template)

	print t.render(border_ip = params['border'])


if __name__ == "__main__":

	params = load_yaml(CONFIG_FILE)

	lm = build_lisp_mobility_strings(params['pools'])

	render_xml(params)