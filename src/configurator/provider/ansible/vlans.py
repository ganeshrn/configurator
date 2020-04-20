#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: Manage editing configuration using ansible.
"""
import os

import ansible_runner

from database import app


class AnsibleManageVlans(object):
    def __init__(self, private_data_dir=None):
        self.private_data_dir = private_data_dir

        if not self.private_data_dir:
            dir_path = os.path.dirname(os.path.realpath(__file__))
            self.private_data_dir = os.path.join(dir_path, '../../../../meta/ansible')

    def get_vlans(self):

        kwargs = {
            "playbook": "get_vlans.yaml",
            "json_mode" : False,
            "extravars": {
                "resources": ['vlans']
            }
        }
        r = ansible_runner.run(private_data_dir=self.private_data_dir, **kwargs)
        #pdb.set_trace()
        if r.rc != 0:
            msg = f"failed to gather vlan facts status: {r.status}\nStats: {r.stats}"
            raise Exception(msg)

        app.logger.info("{}: {}".format(r.status, r.rc))
        app.logger.debug(f"ansible-runner stats: f{r.stats}")
        # successful: 0
        result = {}
        for host in r.stats.get('ok', {}).keys():
            facts = r.get_fact_cache(host)
            result[host] = facts.get('ansible_network_resources', {}).get('vlans')

        app.logger.debug(f"fetched vlans facts: {result}")

        return result

    def edit_vlans(self, config, action='merged'):

        if not isinstance(config, list):
            config = [config]

        kwargs = {
            "playbook": "edit_vlans.yaml",
            "json_mode" : False,
            "extravars": {
                "vlans_config": config,
                "vlans_action": action

            }
        }
        r = ansible_runner.run(private_data_dir=self.private_data_dir, **kwargs)
        #pdb.set_trace()
        if r.rc != 0:
            msg = f"edit vlans failed with action {action} and status {r.status}\nStats: {r.stats}"
            raise Exception(msg)

        app.logger.info("{}: {}".format(r.status, r.rc))
        app.logger.debug(f"ansible-runner stats: f{r.stats}")

        # successful: 0
        changed = r.stats.get('changed', {})
        for host in changed.keys():
            if changed[host]:
                app.logger.debug(f"vlans config updated with action f{action}: {config}")
                return True

        app.loggerupdated.debug(f"no change required for vlan running config")

        return False


# vl = AnsibleManageVlans()
# result = vl.get_vlans()
# print(f"Changed: {result}")
#
# config = [
#   {
#     "vlan_id": 2,
#     "name": "test2"
#   },
#   {
#     "vlan_id": 3,
#     "name": "test3"
#   }
# ]
#
# result = vl.edit_vlans(config, action='overridden')
# print(result)
#
# result = vl.get_vlans()
# print(result)
