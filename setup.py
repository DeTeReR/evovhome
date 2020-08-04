
from setuptools import find_packages, setup

setup(
      name='EvohomeWriter',
      version='1.1',
      packages=find_packages(),
      install_requires=[
            'influxdb',
            'evohomeclient',
      ],
)