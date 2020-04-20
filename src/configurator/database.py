#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: A simple Flask app that manages vlan configuration on network device.
"""
import os
import json

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand
from sqlalchemy.exc import IntegrityError

from config.base import get_option


app = Flask(__name__)

# Initialize a MySQL database towards the other container
dialect = get_option('dialect', 'database')
user = get_option('user', 'database')
password = get_option('password', 'database')
host = get_option('host', 'database')
db_name = get_option('name', 'database')
db_url = f'{dialect}://{user}:{password}@{host}/{db_name}'

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
db.create_all()

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

class Vlans(db.Model):
    vlan_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))

    def __repr__(self):
        return "<Vlans(vlan_id='%d', name='%s', description='%s')>" % (self.vlan_id, self.name, self.description)


def update_vlans_db(config, action='add'):
    # update the vlan config in database
    for vlan_config in config:
        if action == 'add':
            vl = Vlans(vlan_id=vlan_config['vlan_id'], name=vlan_config.get('name'),
                       description=vlan_config.get('description'))
            db.session.add(vl)
        elif action == 'delete':
            vlan = Vlans.query.get(vlan_config['vlan_id'])
            if vlan:
                db.session.delete(vlan)
        elif action == 'update':
            vlan = Vlans.query.get(vlan_config['vlan_id'])
            if vlan:
                vlan.name = vlan_config['name']
                description = vlan_config.get('description')
                if description:
                    vlan.description = description
            else:
                vl = Vlans(vlan_id=vlan_config['vlan_id'], name=vlan_config.get('name'),
                           description=vlan_config.get('description'))
                db.session.add(vl)


def seed_data(seed_path, action='create'):
    with open(os.path.abspath(seed_path), "r") as handle:
        data = json.load(handle)

    for item in data:
        if action == 'create':
            try:
                db.session.add(Vlans(vlan_id=item['vlan_id'], name=item.get('name', ''),
                                     description=item.get('description', '')))
                app.logger.debug(f"added seed data in db: {data}")
            except IntegrityError:
                pass
        elif action == 'delete':
            vlan_record = db.session.query(Vlans).get(item['vlan_id'])
            if vlan_record:
                db.session.delete(vlan_record)
                app.logger.debug(f"deleted seed data in db: {item}")
            else:
                app.logger.debug(f"record not found in db: {item}")
        else:
            raise Exception(f"Invalid seed action {action}")


# seed_data("src/configurator/data/initial.json", action="delete")
# seed_data("src/configurator/data/initial.json", action="create")


if __name__ == '__main__':
    manager.run()
