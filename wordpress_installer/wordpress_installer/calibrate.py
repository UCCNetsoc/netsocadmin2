from jinja2 import Environment, PackageLoader
import os


def calibrate():
	print("Configuring Wordpress installer")

	log_location = os.path.dirname(__file__) + '/resources/wordpress_installer.log'
	try:
		os.remove(log_location)
	except Exception as e:
		pass

	env = Environment(loader=PackageLoader('wordpress_installer', '/resources/templates'))
	template = env.get_template('logging_config.ini.j2') 
	log_config = template.render(LOG_LOCATION=log_location)
	
	log_config_location = os.path.dirname(__file__) + "/resources/logging_config.ini"

	with open(log_config_location, "w") as fh:
		fh.write(log_config)


	print("Writing Files Complete!")

if __name__=="__main__":
	calibrate()
