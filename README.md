# configurator
Network device configuration app

# Prerequisites

1) Install and running MySql server
2) Create database
    ```
    mysql -u root -p"MySql2020"
    mysql> create database db;
    mysql> exit
    ```

# Installation
  ```
  git clone https://github.com/ganeshrn/configurator
  cd configurator
  pip install -r requirements.txt
  source env-setup.sh
  ```


# Running the app
Flash app to CRUD operations:
```
python src/configurator/server.py
```

Running synchronizer to sync device config and database.
# Documentation

This application has two parts:
1) Flask app
* A flask app and MySql database with sqlalchemy integration that
provides REST API to manage vlans. The vlan records added/updated/deleted
in database using REST API's is synced on the network device. The app creates
a `vlans` table in `db` database with columns `vlan_id`, `name`, `description`.

* The default configuration file for this app is stored in `src/configurator/config/configurator.cfg`
  Custom configuration file path can be provided by setting enviornment variable
  `CONFIGURATOR_CFG`.
* Currently this app uses Ansible provider to talk to network devices
* The inventory file and network device login credentials are stored in
  file `meta/ansible/inventory`. Update the device details in inventory before
  running the app.
* The log level for app can be controlled by setting `LOGLEVEL` enviornment
   value. The default level is `INFO`. Value values are `INFO`, `DEBUG`, `WARNING`.

   The API's supported by this app:
   1) GET: /config/vlans
   Fetches vlan_id, name and description from database and returns it
   as a list of dictionaries, if no vlans avaliable it will return empty
   list. Currently after fetching the vlans from database it also sync's
   it on network device to ensure no drift in entries between database and
   config on devices.

   2) GET: /config/vlans/<int:vlan_id>
   Queries database to fetch vlan_id record, if no vlan_id not found error
   response is returned with 404. Currently after fetching the vlan record from database
   it also sync's it on network device to ensure no drift in entries between database and
   config on devices.

   3) POST: /config/vlans
   Create the vlans provided as the request body in database and sync's it on
   the network deivce. If the record already exit in database it return error
   reposne with 400 return code.

   4) PUT: /config/vlans/<int:vlan_id>
   If the vlan_id provided as input in URL is present in database
   the record will be updated from the body of request. If the record
   is not present it will create a new record. The same record will be synced
   with network device.

   5) DELETE: /config/vlans/<int:vlan_id>/<string:name>
   If the combination of vlan_id and name provided as input in URL is present in database
   the record will be deleted and True is return in response. If the record is
   not present it return error respone with 404 return code.

**Note**: Reference postman URL are stored in `postman/` directory.

2) Synchronizer
* This python program fetches the vlan configuration at regular interval from
the device. The `interval` config option under `synchronizer` section in config
file.

* If the vlan record in database is different from the fetched config from device,
the database will be updated to reflect the same config on device.

**Note**: It is assumed that the configuration on the first device in the host
list is considered as reference and it will updated in database and other devices
to remove the vlan configuration drift at regular interval.

# Migration
    python src/configurator/database.py db init
    python src/configurator/database.py db migrate
    python src/configurator/database.py db upgrade
    python src/configurator/database.py db --help

# Note

The app is tested on junos vsrx 15.1R1 version


# Contributors

[Ganesh B. Nalawade](https://github.com/ganeshrn)

