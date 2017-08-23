from setuptools import setup

setup(name='meteo',
      version='1.0',
      description='Meteo logger and server.',
      author='Jonas Hagen',
      author_email='jonas.hagen@iap.unibe.ch',
      packages=['meteo'],
      scripts=['meteo/logger.py', 'meteo/server.py'],
      include_package_data=True,
      install_requires=[
          'pandas>=0.20.0',
          'matplotlib>=1.4.0',
          'flask>=0.10.1',
          'flask-caching>=1.3.0',
          'systemd>=0.10.0',
          'dicttoxml',
          'sqlalchemy>=1.1.0',
          'pyserial>=2.6',
          'pyyaml',
      ],
      zip_safe=False)
