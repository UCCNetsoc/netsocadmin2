from setuptools import setup

setup(name='wordpress_installer',
      version='0.1',
      description='Automated wordpress install',
      url='~',
      author='Hassan Baker',
      author_email='~',
      license='open',
      packages=['wordpress_installer'],
      zip_safe=False,
      install_requires=['wget',
      			'subprocess.run',
      			'jinja2',
      			'requests',
      			'pymysql',
      			'wordpress_installer'],
      			)
