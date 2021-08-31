#!/usr/bin/env python3
#
# TODO: add alert generation time (how long did it take)
# TODO: better error handling for Grafana API calls

import json
import requests
import time

from configparser import ConfigParser
from os.path import expanduser


def get_alerts(backends):
    alert_info = {
        'alerts': [],
        'backends': [],
    }

    for backend in backends:
        if backend['type'] == 'grafana':
            response = get_grafana_alerts(backend['url'], backend['api_token'])
        elif backend['type'] == 'zabbix':
            response = get_zabbix_alerts(backend['url'], backend['api_token'])

        alert_info['alerts'] += response['alerts']

        alert_info['backends'].append({
            'error': response['error'],
            'name': backend['name'],
            'url': backend['url'],
        })

    alert_info['alerts'] = sorted(alert_info['alerts'], key=lambda k: (-k['severity'], -k['created_at']))
    alert_info['backends'] = sorted(alert_info['backends'], key=lambda k: k['name'])
    alert_info['created_at'] = int(time.time())

    return alert_info


def get_config():
    config = {
        'alerts_file_path': '/tmp/alerts.json',
        'backends': [],
    }

    config_parser = ConfigParser()
    config_parser.read('/etc/readalert/config.ini')
    config_parser.read('%s/.config/readalert/config.ini' % expanduser('~'))

    sections = config_parser.sections()
    if not sections:
        raise IOError('Failed to load Read Alert configuration.')

    for section in sections:
        if section == 'default':
            if 'alerts_file' in config_parser[section]:
                config['alerts_file'] = config_parser[section]['alerts_file']

            continue  # 'default' is not a backend section

        backend = {
            'name': section,
        }

        for i in ['api_token', 'type', 'url']:
            if i not in config_parser[section]:
                raise ValueError("Missing config property '%s' in section '%s'" % (i, section))

            backend[i] = config_parser[section][i]

        if backend['type'] not in ['grafana', 'zabbix']:
            raise ValueError("Unsupported backend type '%s' in section '%s'" % (backend['type'], section))

        config['backends'].append(backend)

    return config


def get_grafana_alerts(grafana_url, grafana_api_token):
    response = {
        'alerts': [],
        'error': None,
    }

    r = requests.get(
        '%s/api/alerts' % grafana_url,
        headers={
            'Authorization': 'Bearer %s' % grafana_api_token,
        },
        params={
            'state': 'alerting',
        },
    )
    raw_alerts = sorted(r.json(), key=lambda k: k['id'])

    for raw_alert in raw_alerts:
        alert = {
            'created_at': time.mktime(time.strptime(raw_alert['newStateDate'], '%Y-%m-%dT%H:%M:%SZ')),
            'description': raw_alert['executionError'],
            'id': '%s/%s' % (grafana_url, raw_alert['id']),
            'items': [],
            'name': raw_alert['name'],
            'severity': 3,
            'source': grafana_url,
            'url': '%s%s?panelId=%d' % (grafana_url, raw_alert['url'], raw_alert['panelId']),
        }

        if raw_alert['evalData'] and 'evalMatches' in raw_alert['evalData']:
            for item in raw_alert['evalData']['evalMatches']:
                alert['items'].append('%s: %s' % (item['metric'], item['value']))

        response['alerts'].append(alert)

    return response


def get_zabbix_alerts(zabbix_url, zabbix_api_token):
    trigger_ids = []
    triggers = {}
    response = {
        'alerts': [],
        'error': None,
    }

    # Get problems
    # XXX Zabbix cannot return only unresolved problems: https://support.zabbix.com/browse/ZBXNEXT-5167
    # As a workaround we check the active triggers for all returned problems and skip the problems
    # that do not have any active trigger attached. As a bonus we get problem description from the trigger.
    zabbix_response = get_zabbix_response(zabbix_url, zabbix_api_token, 'problem.get', {
        'acknowledged': False,
        'output': ['clock', 'name', 'objectid', 'severity'],
        'severities': [2, 3, 4, 5],
        'sortfield': ['eventid'],
        'sortorder': 'DESC',
        'suppressed': False,
    })
    if zabbix_response['error']:
        response['error'] = zabbix_response['error']
        return response

    raw_alerts = zabbix_response['result']

    # Get active triggers that caused these problems
    for raw_alert in raw_alerts:
        trigger_ids.append(raw_alert['objectid'])

    zabbix_response = get_zabbix_response(zabbix_url, zabbix_api_token, 'trigger.get', {
        'active': True,
        'output': ['comments', 'error'],
        'selectHosts': ['name'],
        'triggerids': trigger_ids,
        'withUnacknowledgedEvents': True,
    })
    if zabbix_response['error']:
        response['error'] = zabbix_response['error']
        return response

    raw_triggers = zabbix_response['result']

    for raw_trigger in raw_triggers:
        triggers[raw_trigger['triggerid']] = raw_trigger

    # Only process alerts that were caused by active triggers
    for raw_alert in raw_alerts:
        if raw_alert['objectid'] not in triggers:
            continue

        alert = {
            'created_at': int(raw_alert['clock']),
            'description': '',
            'id': '%s/%s' % (zabbix_url, raw_alert['eventid']),
            'items': [],
            'name': raw_alert['name'],
            'severity': int(raw_alert['severity']),
            'source': zabbix_url,
            'url': '%s/tr_events.php?triggerid=%s&eventid=%s' % (
                zabbix_url, raw_alert['objectid'], raw_alert['eventid'])
        }

        if raw_alert['objectid'] in triggers:
            if triggers[raw_alert['objectid']]['error']:
                alert['description'] = triggers[raw_alert['objectid']]['error']
            else:
                alert['description'] = triggers[raw_alert['objectid']]['comments']
            for host in triggers[raw_alert['objectid']]['hosts']:
                alert['items'].append(host['name'])

        response['alerts'].append(alert)

    return response


def get_zabbix_response(zabbix_url, zabbix_api_token, method, params={}):
    response = {
        'error': None,
        'result': None,
    }

    try:
        r = requests.post(
            '%s/api_jsonrpc.php' % zabbix_url,
            data=json.dumps({
                'auth': zabbix_api_token,
                'id': 1,
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
            }),
            headers={
                'Content-Type': 'application/json-rpc',
            },
        )
        response_json = r.json()

        if 'error' in response_json:
            response['error'] = '%s: %s' % (response_json['error']['code'], response_json['error']['message'])

        if 'result' in response_json:
            response['result'] = response_json['result']
    except:
        response['error'] = 'Failed to retrive data from backend.'

    return response


def write_alerts(alerts, alerts_file):
    with open(alerts_file, 'w') as f:
        json.dump(alerts, f, indent=2, sort_keys=True)


def main():
    config = get_config()
    alerts = get_alerts(config['backends'])
    write_alerts(alerts, config['alerts_file'])


if __name__ == '__main__':
    main()
