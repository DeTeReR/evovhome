import argparse
from collections import defaultdict
from datetime import datetime

from evohomeclient import EvohomeClient
from influxdb import InfluxDBClient
from pytz import timezone

_UTC = timezone('UTC')


def evohome_samples(username, password):
    evohome_client = EvohomeClient(username, password)
    info = defaultdict(dict)
    timestamp = datetime.now(tz=_UTC).strftime(format='%Y-%m-%dT%H:%M:%SZ')
    for device in evohome_client.temperatures():
        name = (device.get('name') or device.get('thermostat')).replace(' ', '_')
        temperature = device.get('temp')
        setpoint = device.get('setpoint')
        heating = device.get('mode')
        if temperature is not None:
            info[name]['temperature'] = device.get('temp')
        if setpoint is not None:
            info[name]['setpoint'] = setpoint
        if heating is not None:
            info[name]['heating_on'] = 0 if 'off' in heating.lower() else 1
    return info, timestamp


def insert_into_influx(samples, timestamp, hostname, **influx_kwargs):
    client = InfluxDBClient(host=hostname, database='evohome', **influx_kwargs)
    with client:
        json_body = []
        for name, stats in samples.items():
            json_body.append(
                {
                    "measurement": "evohome_stats",
                    "tags": {
                        "name": name,
                        "location": "Raleigh Gardens"
                    },
                    "time": timestamp,
                    "fields": {
                        "temperature": float(stats['temperature']),
                        "set point": float(stats['setpoint']),
                        "heating on": int(stats['heating_on']),
                    }
                }
            )
        print("Write points: {0}".format(json_body))
        client.write_points(json_body)


def run(username, password, hostname='pi.hole'):
    samples, timestamp = evohome_samples(username, password)
    insert_into_influx(samples, timestamp, hostname)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('evohome_username')
    parser.add_argument('evohome_password')
    parser.add_argument('graphite_hostname', default='localhost')
    args = parser.parse_args()
    print(run(args.evohome_username, args.evohome_password, args.graphite_hostname))
