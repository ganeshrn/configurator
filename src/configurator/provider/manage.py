#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: Manage providers for the app.
"""
from config.base import get_option
try:
    from configurator.provider.ansible.vlans import AnsibleManageVlans
    HAS_ANSIBLE_PROVIDER = True
except ImportError:
    HAS_ANSIBLE_PROVIDER = False

provider = get_option('provider')

VALID_PROVIDERS = ['ansible']
if provider not in VALID_PROVIDERS:
    raise Exception("Invalid provider value %s. Supported providers %s"
                    % (provider, ', '.join(VALID_PROVIDERS)))


class ManageVlans(object):
    def __init__(self,  private_data_dir=None):
        if HAS_ANSIBLE_PROVIDER:
            self.obj = AnsibleManageVlans(private_data_dir)
        else:
            raise Exception(f"provider {provider} not supported")

    def get_vlans(self):
        '''
        Get list of vlans
        :return: list of vlans
        '''
        return self.obj.get_vlans()

    def edit_vlans(self, config, action='merged'):
        '''
        Edit vlans on device
        :param config: list of dict of vlan config, Each dict can have
                        keys 'vlan_id' (mandatory), 'name' and 'description'.
        :param action: Tha value of action can be merged, replaced, deleted, overridden.
        :return: True or False based on if vlan config is changed on device or not.
        '''
        return self.obj.edit_vlans(config, action=action)
