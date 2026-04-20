Read Alert
==========

Alert viewer with multiple backend (Grafana, Rootly and Zabbix) support.

Demo: [default](https://hudolejev.github.io/readalert/demo), [kiosk](https://hudolejev.github.io/readalert/demo?tv).

Known to work with:
 - Grafana v8.4, v7.4, v6.6
 - Rootly API v1
 - Zabbix v5.0, v4.0


Requirements
------------

Backend:
 - Linux (known to work on Ubuntu 24.04; should work on OS X too)
 - Python 3.5+ (known to work on Python 3.12)
 - [Python requests library](https://pypi.org/project/requests)

Frontend:
 - Any modern browser with JavaScript support (known to work in Chromium and Firefox)


Installation
------------

 1. Unpack the contents of the package (recommended location: `/opt/readalert/`)
 2. Install the web server (recommended: Nginx)


Configuration
-------------

Read Alert collector will search for configuration files in the following locations;
options from the latter file override these from the former:

 1. `/etc/readalert/config.ini` (recommended for servers)
 2. `~/.config/readalert/config.ini` (recommended for local use)

Example Read Alert collector configuration file:

    [default]
    alerts_file = /opt/readalert/pub/alerts.json

    # Known backends
    # Can add multiple backends of the same type but the URLs must be different

    [My Grafana]
    api_token = ...
    type = grafana
    url = https://grafana.example.org

    [My Rootly]
    api_token = ...
    type = rootly
    url = https://api.rootly.com

    [My Zabbix]
    api_token = ...
    type = zabbix
    url = https://zabbix.example.org

Configure Cron to update alerts periodically, example:

    */3 * * * * root /opt/readalert/bin/readalert.py

Configure Nginx to serve Read Alert frontend, example:

    server {
        listen 80;

        location / {
            root /opt/readalert/pub;
            index index.html;
        }
    }


alerts.json
-----------

Read Alert collector generates, and Read Alert frontend consumes `alerts.json` with the following structure:

    {
      "alerts": [
        {
          "created_at": <num>,     | Alert creation time, UNIX timestamp
          "description": <str>,    | Optional
          "id": <any>,             | Optional; not currently used
          "items": <list[str]>,    | Should be set, may be []
          "name": <str>,           |
          "severity": <num>,       | 2: warning, 3: average, 4: high, 5: disaster
          "source": <str>,         | URL to match the backend.url (see below)
          "url": <str>             | Alert URL
        }, ...
      ],

      "backends": [
        {
          "error": <str>,          | Optional; may be null
          "name": <str>,           |
          "url": <str>,            | URL to match the alert.source (see above)
        }, ...
      ],

      "created_at": <num>          | Alert list generation time, UNIX timestamp
    }

You can write your own custom collector to generate the `alerts.json` as described above;
see [bin/readalert.py](./bin/readalert.py) for reference implementation.


Author
------

Juri Hudolejev <jhudolejev@gmail.com>


License
-------

MIT
