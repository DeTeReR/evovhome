import argparse
import os
from collections import defaultdict
from datetime import datetime, timezone
from itertools import zip_longest
from pprint import pprint as pp

import boto3
from evohomeclient import EvohomeClient


def run(username, password):
    evohome_client = EvohomeClient(username, password)
    info = defaultdict(dict)
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

    cloudwatch = boto3.client('cloudwatch')
    print(_put_metric_data(cloudwatch, info, datetime.now(timezone.utc)))
    return info


def _put_metric_data(cloudwatch, info, timestamp):
    statuses = []
    for metric_data in grouper(_yield_metric_data(info, timestamp), 20):  # 20 is the aws limit
        statuses.append(cloudwatch.put_metric_data(Namespace='Raleigh/Evohome', MetricData=metric_data))
    return statuses


def _yield_metric_data(info, timestamp):
    for room, data in info.items():
        for metric, value in data.items():
            yield {
                'MetricName': metric,
                'Dimensions': [
                    {
                        'Name': 'Room',
                        'Value': room,
                    },
                ],
                'Timestamp': timestamp,
                'Value': value
            }


def grouper(iterable, n):
    """Collect data into fixed-length chunks or blocks. Copied from itertools recipes."""
    _args = [iter(iterable)] * n
    obj = object()
    return ([val for val in _list if val is not obj] for _list in zip_longest(*_args, fillvalue=obj))


def lambda_handler(event, context):
    username = os.environ['username']
    password = os.environ['password']
    pp(run(username, password))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('username')
    parser.add_argument('password')
    args = parser.parse_args()
    print(run(args.username, args.password))
