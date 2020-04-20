#!/usr/bin/env python

"""
Author: Ganesh Nalawade
Purpose: A simple Flask app that manages vlan configuration on network device.
"""

from flask import abort, jsonify, make_response, request
from sqlalchemy.exc import IntegrityError
from database import db, app, Vlans, update_vlans_db
from configurator.provider import manage

import pdb
manage_vlans = manage.ManageVlans()


@app.route('/')
def index():
    return "Welcome to configurator!"


@app.route('/config/vlans/<int:vlan_id>', methods=['GET'])
def get_vlan(vlan_id):
    vlan = Vlans.query.get(vlan_id)
    if vlan:
        config = [{"vlan_id": vlan.vlan_id, "name": vlan.name, "description": vlan.description}]

        # TODO: Clarify if updating vlan config on device allowed
        # by other means (like manually login), if not remove below
        # edit on device.
        # ensure the vlan config stored in database is also
        # on the device. This is an idempotent call
        result = manage_vlans.edit_vlans(config, action="replaced")
        if result:
            app.logger.info("updated vlan config on device from database")
        else:
            app.logger.info("vlan config on device same as that of database")
        return jsonify(config)
    else:
        abort(404, f"vlan resource {vlan_id} not found")


@app.route("/config/vlans", methods=["GET"])
def get_vlans():
    """
    This is a view function which responds to requests to get the vlan
    details from database
    """
    config = []
    vlan_records = Vlans.query.all()
    app.logger.info("fetched vlan record %s" % vlan_records)
    if vlan_records:
        for vlan_record in vlan_records:
            config.append({"vlan_id": vlan_record.vlan_id, "name": vlan_record.name, "description": vlan_record.description})

        # TODO: Clarify if updating vlan config on device allowed
        # by other means (like manually login), if not remove below
        # edit on device.
        # ensure the vlan config stored in database is also
        # on the device. This is an idempotent call
        try:
            result = manage_vlans.edit_vlans(config, action="overridden")
            if result:
                app.logger.info("updated vlans config on device from database")
            else:
                app.logger.info("vlans config on device same as that of database")
            return jsonify(config)
        except Exception as e:
            abort(400, f"Failed to get vlan config from device with error\n{e}")
    else:
        return jsonify([])


@app.route('/config/vlans', methods=['POST'])
def create_vlans():
    if not request.json or not isinstance(request.json, list):
        abort(400, f'invalid json body {request.json}, json body should be of type list')

    config = request.json
    for vlan in config:
        for key in vlan.keys():
            if key not in ['name', 'vlan_id', 'description']:
                abort(400, "invalid key '%s' in config dict %s" % (key, vlan))
            if key == 'vlan_id' and not (0 < vlan[key] <= 1024):
                abort(400, "invalid vlan_id value %s in config dict %s" % (vlan[key], vlan))

    # update the vlan config in database
    try:
        update_vlans_db(config)
        app.logger.info(f"Updated db with vlan config {config}")
    except IntegrityError as e:
        abort(400, f"Failed to update config {config} in db with error\n{e.orig}")

    # update the vlan config on device.
    # This is an idempotent call
    try:
        result = manage_vlans.edit_vlans(config, action="overridden")
        if result:
            app.logger.info("overriden vlan config on device")
        else:
            app.logger.info("vlan config same as post request body")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.info(f"device post request failed, rollback database items {config}")
        abort(400, "Failed to update config {config} on device with error\n%s" % str(e))
    # finally:
    #     db.session.close()

    return jsonify(config), 201


@app.route('/config/vlans/<int:vlan_id>', methods=['PUT'])
def update_task(vlan_id):
    #pdb.set_trace()
    if not request.json or not isinstance(request.json, dict):
        abort(400, f'invalid json body {request.json}, json body should be of type dict')

    config = request.json
    name = config.get('name')
    if not name:
        abort(400, f"name key is required")

    if not (0 < vlan_id <= 1024):
        abort(400, "invalid vlan_id value %s in config dict %s" % (vlan_id, config))

    if vlan_id != config.get('vlan_id'):
        abort(400, "vlan_id in url %s should be same as that in body %s" % (vlan_id, config.get('vlan_id')))

    update = True if Vlans.query.get(vlan_id) else False

    # update the vlan config in database
    try:
        if update:
            update_vlans_db([config], action='update')
            app.logger.info(f"Updated db with vlan config {config}")
        else:
             update_vlans_db([config], action='add')
             app.logger.info(f"Added vlan config to db{config}")
    except IntegrityError as e:
        abort(400, f"Failed to update config {config} in db with error\n{e.orig}")

    # update the vlan config on device.
    # This is an idempotent call
    try:
        result = manage_vlans.edit_vlans(config, action="replaced")
        if result:
            app.logger.info("replaced vlan config on device")
        else:
            app.logger.info("vlan config same as post request body")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.info(f"device post request failed, rollback database items {config}")
        abort(400, "Failed to update config {config} on device with error\n%s" % str(e))
    # finally:
    #     db.session.close()

    return jsonify(config), 201


@app.route('/config/vlans/<int:vlan_id>/<string:name>', methods=['DELETE'])
def delete_task(vlan_id, name):
    if not (0 < vlan_id <= 1024):
        abort(400, "invalid vlan_id value %s" % vlan_id)

    delete = True if Vlans.query.get(vlan_id) else False

    # update the vlan config in database
    try:
        if delete:
            update_vlans_db([{'vlan_id': vlan_id}], action='delete')
            app.logger.info(f"deleted vlan config with id {vlan_id} from db")
        else:
            app.logger.info(f"vlan_id {vlan_id} record do not exist in db")
            abort(404, f"vlan_id {vlan_id} does not exist")
    except IntegrityError as e:
        abort(400, f"Failed to delete vlan_id {vlan_id} in db with error\n{e.orig}")

    # update the vlan config on device.
    # This is an idempotent call
    try:
        result = manage_vlans.edit_vlans([{'vlan_id': vlan_id, 'name': name}], action="deleted")
        if result:
            app.logger.info(f"deleted vlan_id {vlan_id} on device")
        else:
            app.logger.info("vlan_id {vlan_id} record do not exit in db")
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.info(f"device delete request failed, rollback database items")
        abort(400, "Failed to delete vlan config on device with error\n%s" % str(e))
    # finally:
    #     db.session.close()

    return jsonify({'result': True})


@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': error.get_description()}), 400)


if __name__ == "__main__":

    # Start Flask app. The "host" and "debug" options are both security
    # concerns, but for testing, we ignore them with the "nosec comment"
    app.run(
        host="0.0.0.0", debug=True, use_reloader=False  #nosec
    )
