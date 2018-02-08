"""
Sample configuration for wordpress installer
"""

"""
This is the configuration for the wordpress database that netsocadmin will
talk to when installing user's wordpress installation into their home
directories.
"""
db = {
	"user" 			: "me",
	"password" 		: "password123",
	"host"			: "mysql.mydomain.com"
}

"""
This configures the package itself.
"""
package = {
    # (Make this an absolute path)
	"logging_config" : "<location-of-netsocadmin>/netsocadmin/wordpress_installer/wordpress_installer/resources/logging_config.ini"
}
