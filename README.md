Read Alert
==========

Alert viewer with multiple backend (Grafana and Zabbix) support.

Actively tested with:
 - Grafana v7.4
 - Zabbix v5.0

Also known to work with:
 - Grafana v6.6
 - Zabbix v4.0


Requirements
------------
 - Linux (known to work on Ubuntu 20.04, 18.04 and 16.04; should probably work on OS X too)
 - Python 3.5+ (also known to work on Python 3.7)
 - [Python requests library](https://pypi.org/project/requests)


Installation
------------

 1. Unpack the contents of the package (recommended location: `/opt/readalert/`)
 2. Install web server (recommended: Nginx)


Configuration
-------------

Read Alert will search for configuration files in the following locations;
options from the latter file override these from the former:

 1. `/etc/readalert/config.ini` (recommended for servers)
 2. `~/.config/readalert/config.ini` (recommended for local use)

Example Read Alert configuration file:

    [default]
    alerts_file = /opt/readalert/pub/alerts.json

    # Known backends
    # Can add multiple backends of the same type but the URLs must be different

    [My Grafana]
    api_token = ...
    type = grafana
    url = https://grafana.example.org

    [My Zabbix]
    api_token = ...
    type = zabbix
    url = https://zabbix.example.org

Configure Cron to update alerts periodically, example:

    */3 * * * * root /opt/readalert/bin/readalert.py

Configure Nginx to serve Read Alert web page, example:

    server {
        listen 80;

        location / {
            root /opt/readalert/pub;
            index index.html;
        }
    }


Author
------

Juri Hudolejev <jhudolejev@gmail.com>


License
-------

MIT
