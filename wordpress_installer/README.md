# WordPress Installer

This package contains all functionality needed to automate wordpress installs on UCC Netsoc servers.

# Installation of package
```sh
$ cd netsocadmin/wordpress_installer
$ sudo pip3.5 install -e .
$ sudo python3.5 -m wordpress_installer.calibrate
```

Afterwards, make sure to create a new package configuration following the sample-config.py file. The new configuration file's name should be 'config.py'.