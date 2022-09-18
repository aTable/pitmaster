import board
import digitalio
import adafruit_max31855
import RPi.GPIO as GPIO
from time import sleep, strftime, time
import yaml
import requests
from timeit import default_timer as timer
import urllib3
import os
import json
from threading import Thread
from datetime import datetime
import random
from http.server import HTTPServer
from utils import convert_celsius_to_fahrenheit, convert_fahrenheit_to_celsius
from AllReadingsServer import AllReadingsServer

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_SCRIPT_PATH, 'config.yml')
NODE_EXPORTER_PATH = os.path.join(CURRENT_SCRIPT_PATH, 'pitmaster_export.json')
READINGS_DATA_PATH = os.path.join(
    CURRENT_SCRIPT_PATH, 'pitmaster_readings.json')
READINGS_SERVER_PORT = 30027
READINGS_SERVER_ADDRESS = "0.0.0.0"
urllib3.disable_warnings()

degree_sign = u'\N{DEGREE SIGN}'
LED_PIN_GREEN = 17
LED_PIN_RED = 27
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max31855 = adafruit_max31855.MAX31855(spi, cs)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LED_PIN_GREEN, GPIO.OUT)
GPIO.setup(LED_PIN_RED, GPIO.OUT)


def load_config():
    with open(CONFIG_PATH, 'r') as raw_yml:
        config = yaml.safe_load(raw_yml)
        # convert MINIMUM range to celsius if provided in fahrenheit only
        if not config['temperature_minimum_celsius'] and config['temperature_minimum_fahrenheit']:
            config['temperature_display_mode'] = 'fahrenheit'
            config['temperature_minimum_celsius'] = convert_fahrenheit_to_celsius(
                config['temperature_minimum_fahrenheit'])
        # convert MAXIMUM range to celsius if provided in fahrenheit only
        if not config['temperature_maximum_celsius'] and config['temperature_maximum_fahrenheit']:
            config['temperature_display_mode'] = 'fahrenheit'
            config['temperature_maximum_celsius'] = convert_fahrenheit_to_celsius(
                config['temperature_maximum_fahrenheit'])

        if not config['temperature_minimum_celsius'] or not config['temperature_maximum_celsius']:
            print(f"missing required temperature range")
            exit(1)

        if not config['temperature_display_mode'] or config['temperature_display_mode'] != 'fahrenheit':
            config['temperature_display_mode'] = 'celsius'

        return config


def init(config):
    if not os.path.exists(READINGS_DATA_PATH):
        with open(READINGS_DATA_PATH, 'a') as f:
            json.dump([], f)


def read_temperature_celsius():
    # return random.random() * 100
    return max31855.temperature


def summarize_temperature(config, temperature_celsius):
    now = datetime.now()
    if is_temperature_acceptable(config, temperature_celsius):
        return f"{now.strftime(config['time_format'])} temperature '{pretty_print_temperature_value(config, temperature_celsius)}' IS within allowed range ({pretty_print_temperature_value(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature_value(config, config['temperature_maximum_celsius'])})."
    else:
        return f"{now.strftime(config['time_format'])} temperature '{pretty_print_temperature_value(config, temperature_celsius)}' is NOT within allowed range ({pretty_print_temperature_value(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature_value(config, config['temperature_maximum_celsius'])})."


def pretty_print_temperature_value(config, temperature_celsius):
    if config['temperature_display_mode'] == 'fahrenheit':
        return f"{str(convert_celsius_to_fahrenheit(temperature_celsius))}{degree_sign}F"
    else:
        return f"{str(temperature_celsius)}{degree_sign}C"


def is_temperature_acceptable(config, temperature_celsius):
    return temperature_celsius >= config['temperature_minimum_celsius'] and temperature_celsius < config['temperature_maximum_celsius']


def light_led_green_only(seconds):
    GPIO.output(LED_PIN_RED, GPIO.LOW)
    GPIO.output(LED_PIN_GREEN, GPIO.HIGH)
    sleep(seconds)
    GPIO.output(LED_PIN_GREEN, GPIO.LOW)


def light_led_red_only(seconds):
    GPIO.output(LED_PIN_GREEN, GPIO.LOW)
    GPIO.output(LED_PIN_RED, GPIO.HIGH)
    sleep(seconds)
    GPIO.output(LED_PIN_RED, GPIO.LOW)


def cleanup_gpio():
    GPIO.output(LED_PIN_GREEN, GPIO.LOW)
    GPIO.output(LED_PIN_RED, GPIO.LOW)
    GPIO.cleanup()


def push_notification(config, title, markdown_message, priority):
    payload = {
        'topic': config['push_notification']['ntfy']['topic'],
        'priority': priority,
        'title': title,
        'message': f"{markdown_message}"
    }
    for ntfy_server in config['push_notification']['ntfy']['servers']:
        res = requests.post(
            url=ntfy_server, headers={"Content-Type": "application/json"}, json=payload)
        if not res.ok:
            print(f"\tDEBUG: ntfy failure")
            print(f"\t{res.text}")


def periodic_status_report_forever(config):
    print(
        f"DEBUG: starting periodic status report to notify every {config['send_mandatory_report_every_seconds']} seconds.")
    try:
        while True:
            current_temperature_celsius = read_temperature_celsius()
            message = summarize_temperature(
                config, current_temperature_celsius)
            print(f"DEBUG: periodic notification: {message}")
            push_notification(config, 'Periodic Report', message, 1)
            sleep(config['send_mandatory_report_every_seconds'])
    except Exception as e:
        print(e)
        print(f"DEBUG: shutting down periodic status report.")


def monitor_forever(config):
    print(
        f"DEBUG: starting monitoring to read every {config['read_temperature_after_seconds']} seconds.")
    try:
        while True:
            current_temperature_celsius = read_temperature_celsius()
            message = summarize_temperature(
                config, current_temperature_celsius)
            print(f"DEBUG: monitoring: {message}")
            new_reading = {
                'recorded_at_utc': datetime.utcnow().isoformat() + 'Z',
                'celsius': current_temperature_celsius,
                'fahrenheit': convert_celsius_to_fahrenheit(current_temperature_celsius)
            }
            with open(NODE_EXPORTER_PATH, 'w') as f:
                json.dump(new_reading, f)

            all_readings = []
            with open(READINGS_DATA_PATH, 'r') as f:
                all_readings = json.load(f)
            all_readings.append(new_reading)
            with open(READINGS_DATA_PATH, 'w') as f:
                json.dump(all_readings, f)

            if is_temperature_acceptable(config, current_temperature_celsius):
                light_led_green_only(config['indicate_led_for_seconds'])
            else:
                push_notification(config, 'Problem', message, 4)
                light_led_red_only(config['indicate_led_for_seconds'])
            sleep(config['read_temperature_after_seconds'])
    except Exception as e:
        print(e)
        end_time = timer()
        elapsed = end_time - start_time
        print(f"DEBUG: shutting down. Elapsed for {elapsed} seconds.")
        cleanup_gpio()


def start_data_server():
    print(f"DEBUG: starting raw data exporter")
    webServer = HTTPServer(
        (READINGS_SERVER_ADDRESS, READINGS_SERVER_PORT), AllReadingsServer)
    webServer.serve_forever()
    print("Server started http://%s:%s" %
          (READINGS_SERVER_ADDRESS, READINGS_SERVER_PORT))


if __name__ == '__main__':
    start_time = timer()
    config = load_config()
    init(config)
    if config['start_message']:
        print(config['start_message'])

    Thread(target=monitor_forever, args=(config,)).start()
    Thread(target=start_data_server, args=()).start()

    if config['send_mandatory_report_every_seconds'] and config['send_mandatory_report_every_seconds'] > 0:
        Thread(target=periodic_status_report_forever, args=(config,)).start()
    else:
        print(f"DEBUG: update config.yml 'send_mandatory_report_every_seconds' to be > 0 if you want periodic notifications.")
