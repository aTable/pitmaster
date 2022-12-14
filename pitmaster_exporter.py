from prometheus_client import start_http_server, Summary, Gauge
import random
from time import sleep
import os
import json
from utils import convert_celsius_to_fahrenheit
from threading import Thread

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
EXPORTER_PORT = 30026
EXPORTER_ADDRESS = "0.0.0.0"
POLL_EXPORTED_FILE_SECONDS = 5
NODE_EXPORTER_PATH = os.path.join(CURRENT_SCRIPT_PATH, 'pitmaster_export.json')


pitmaster_temperature_celsius_gauge = Gauge('pitmaster_temperature_celsius',
                                            'The current temperature of the pit in celsius')
pitmaster_temperature_fahrenheit_gauge = Gauge('pitmaster_temperature_fahrenheit',
                                               'The current temperature of the pit in fahrenheit')

REQUEST_TIME = Summary('request_processing_seconds',
                       'Time spent processing request')


def refresh_current_temp_gauges():
    temperature_celsius = -1
    if os.path.exists(NODE_EXPORTER_PATH):
        with open(NODE_EXPORTER_PATH, 'r') as f:
            payload = json.load(f)
            temperature_celsius = payload['celsius']
    else:
        print(f"\tDEBUG: {NODE_EXPORTER_PATH} does not exist")
    pitmaster_temperature_celsius_gauge.set(temperature_celsius)
    pitmaster_temperature_fahrenheit_gauge.set(
        convert_celsius_to_fahrenheit(temperature_celsius))


def start_prometheus_exporter():
    print(f"DEBUG: starting prometheus exporter")
    start_http_server(port=EXPORTER_PORT, addr=EXPORTER_ADDRESS)
    while True:
        refresh_current_temp_gauges()
        sleep(POLL_EXPORTED_FILE_SECONDS)


if __name__ == '__main__':
    print(f"DEBUG: starting pitmaster_exporter")
    Thread(target=start_prometheus_exporter, args=()).start()
