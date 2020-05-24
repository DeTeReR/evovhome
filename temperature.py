import argparse
from datetime import datetime, timezone
import os
from collections import defaultdict
from pprint import pprint as pp

import boto3
from evohomeclient import EvohomeClient

def run(username, password):
    evohome_client = EvohomeClient(username, password)
    info = defaultdict(dict)
    timestamp = datetime.now(timezone.utc)
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
    for room, data in info.items():
        for metric, value in data.items():
            print(_put_metric_data(cloudwatch, room, metric, value, timestamp))
    return info


def _put_metric_data(cloudwatch, room, metric, value, timestamp):
    response = cloudwatch.put_metric_data(
        MetricData=[
            {
                'MetricName': metric,
                'Dimensions': [
                    {
                        'Name': 'Room',
                        'Value': room,
                    },
                ],
                'Timestamp': timestamp,
                'Value': value
            },
        ],
        Namespace='Raleigh/Evohome'
    )
    return response


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
