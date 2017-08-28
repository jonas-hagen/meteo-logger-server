import yaml
import multiprocessing


# Configure
with open('/etc/meteo.yml', 'r') as f:
    meteo_config = yaml.load(f)


bind = meteo_config['server']['host'] + ':' + str(meteo_config['server']['port'])
workers = multiprocessing.cpu_count() * 2 + 1
accesslog = '-'  # log to stdout


del meteo_config
