#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: A python program to read vlan config from network device
         and update it in local database if the records differs.
"""
import logging
import os
import time
import sqlalchemy as db

from copy import deepcopy

from config.base import get_option
from configurator.provider import manage

log = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "DEBUG"),
                    format='%(process)d-%(levelname)s-%(message)s')

dialect = get_option('dialect', 'database')
user = get_option('user', 'database')
password = get_option('password', 'database')
host = get_option('host', 'database')
db_name = get_option('name', 'database')
db_url = f'{dialect}://{user}:{password}@{host}/{db_name}'


engine = db.create_engine(db_url)
connection = engine.connect()
metadata = db.MetaData()


class VlansDb(object):
    def __init__(self, engine, connection, metadata):
        self.engine = engine
        self.connection = connection
        self.metadata = metadata
        self.vlans_db = db.Table('vlans', self.metadata,
                                 autoload=True, autoload_with=engine)

    def get_vlans(self):
        query = db.select([self.vlans_db])
        return connection.execute(query).fetchall()

    def update_db_vlans(self, vlans):
        for item in vlans:
            try:
                query = db.update(self.vlans_db).values(name=item[1], description=item[2])
                query = query.where(self.vlans_db.columns.vlan_id == item[0])
                results = connection.execute(query)
                log.info(f"updated vlan record {item} in db")
            except Exception as e:
                raise Exception(f"failed to update vlan record {item} in db with error {e}")

    def create_db_vlans(self, vlans):
        vlans_list = []
        for item in vlans:
            query = db.insert(self.vlans_db)
            vlans_list.append({'vlan_id': item[0], 'name': item[1], 'description': item[2]})

        try:
            self.connection.execute(query,vlans_list)
            log.info(f"created vlan record {vlans_list} in db")
        except Exception as e:
            raise Exception(f"failed to create vlan record {vlans} in db with error {e}")

    def delete_db_vlans(self, vlans):
        for item in vlans:
            try:
                query = db.delete(self.vlans_db)
                query = query.where(self.vlans_db.columns.vlan_id == item[0])
                results = connection.execute(query)
                log.info(f"deleted vlan record {item} in db")
            except Exception as e:
                raise Exception(f"failed to delete vlan record {item} in db with error {e}")


def sort_on_first(elem):
    return elem[0]


def run():
    while True:
        interval = get_option('interval', 'synchronizer')
        time.sleep(10)

        vlans_obj = VlansDb(engine, connection, metadata)
        vlans_in_db = deepcopy(vlans_obj.get_vlans())
        vlans_in_db = sorted(vlans_in_db, key=sort_on_first)
        log.debug(f"vlans fetched from db {vlans_in_db}")
        db_vlan_update = []
        db_vlan_delete = deepcopy(vlans_in_db)

        manage_vlans = manage.ManageVlans()
        result = manage_vlans.get_vlans()

        # assuming first device in the list has the final config
        std_dev = list(result.keys())[0]

        vlans_result = result[std_dev]
        vlans_in_dev = []
        for vlans in vlans_result:
            vlans_in_dev.append((vlans['vlan_id'], vlans.get('name'), vlans.get('description')))

        vlans_in_dev = sorted(vlans_in_dev, key=sort_on_first)
        db_vlan_create = deepcopy(vlans_in_dev)
        log.debug(f"vlans fetched from device {vlans_in_dev}")

        for db_item in vlans_in_db:
            for dev_item in vlans_in_dev:
                if db_item[0] == dev_item[0]:
                    if db_item[1] != dev_item[1] or db_item[2] != dev_item[2]:
                        db_vlan_update.append((dev_item[0], dev_item[1], dev_item[2]))
                    db_vlan_create.remove(dev_item)
                    db_vlan_delete.remove(db_item)

        log.info(f"vlans to be update in db {db_vlan_update}")
        log.info(f"vlans to be created in db {db_vlan_create}")
        log.info(f"vlans to be deleted in db {db_vlan_delete}")

        if db_vlan_update:
            vlans_obj.update_db_vlans(db_vlan_update)

        if db_vlan_create:
            vlans_obj.create_db_vlans(db_vlan_create)

        if db_vlan_delete:
            vlans_obj.delete_db_vlans(db_vlan_delete)


if __name__ == '__main__':
    run()
