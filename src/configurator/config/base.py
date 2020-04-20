#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: Manage configurator app Configuration.
"""
import os
import logging
import yaml

log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                    format='%(process)d-%(levelname)s-%(message)s')


config_file_path = None
config_dir_path = None

# read config file path from environment variable
# directory path that has configurator.cfg file
config_dir_path = os.environ.get('CONFIGURATOR_CFG')
if config_dir_path:
    config_file_path = os.path.join(config_dir_path, 'configurator.cfg')

# read default config file
if not config_file_path:
    config_dir_path = os.path.dirname(os.path.realpath(__file__))
    config_file_path = os.path.join(config_dir_path, 'configurator.cfg')

log.info("loaded config file from path %s" % config_file_path)

with open(config_file_path) as fp:
    CONFIG_DATA = yaml.safe_load(fp)


def get_option(name, section="defaults"):
    '''
    Get value of config option
    :param name: Name of the config parameter
    :param section: Section in which conifg parameter is present
    :return: Value of config parameter
    '''
    try:
        return CONFIG_DATA.get(section, {})[name]
    except KeyError:
        Exception("Unable to fetch config variable %s from section %s" % (name, section))
