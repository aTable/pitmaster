import board
import digitalio
import adafruit_max31855
import RPi.GPIO as GPIO
from time import sleep
import yaml
import requests
from timeit import default_timer as timer
import urllib3
import os
import json
from utils import convert_celsius_to_fahrenheit, convert_fahrenheit_to_celsius
from threading import Thread

CURRENT_SCRIPT_PATH = os.path.dirname(os.path.realpath(__file__))
CONFIG_PATH = os.path.join(CURRENT_SCRIPT_PATH, 'config.yml')
NODE_EXPORTER_PATH = os.path.join(CURRENT_SCRIPT_PATH, 'pitmaster_export.json')
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


def read_temperature_celsius():
    # return 52
    return max31855.temperature


def summarize_temperature(config, temperature_celsius):
    if is_temperature_acceptable(config, temperature_celsius):
        return f"Current temperature '{pretty_print_temperature_value(config, temperature_celsius)}' IS within allowed range ({pretty_print_temperature_value(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature_value(config, config['temperature_maximum_celsius'])})."
    else:
        return f"Current temperature '{pretty_print_temperature_value(config, temperature_celsius)}' is NOT within allowed range ({pretty_print_temperature_value(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature_value(config, config['temperature_maximum_celsius'])})."


def pretty_print_temperature_value(config, temperature_celsius):
    if config['temperature_display_mode'] == 'fahrenheit':
        return f"{str(convert_celsius_to_fahrenheit(temperature_celsius))}{degree_sign}F"
    else:
        return f"{str(temperature_celsius)}{degree_sign}C"


def is_temperature_acceptable(config, temperature_celsius):
    return temperature_celsius >= config['temperature_minimum_celsius'] and temperature_celsius < config['temperature_maximum_celsius']


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
        f"DEBUG: starting periodic status report to notify every {config['notify_temperature_every_seconds']} seconds")
    try:
        while True:
            current_temperature_celsius = read_temperature_celsius()
            message = summarize_temperature(
                config, current_temperature_celsius)
            print(message)
            push_notification(config, 'Periodic Report', message, 1)
            sleep(config['notify_temperature_every_seconds'])
    except Exception as e:
        print(e)
        print(f"DEBUG: shutting down periodic status report.")


def monitor_forever(config):
    print(
        f"DEBUG: starting monitoring to read every {config['read_temperature_after_seconds']} seconds.")
    try:
        while True:
            current_temperature_celsius = read_temperature_celsius()
            with open(NODE_EXPORTER_PATH, 'w') as f:
                json.dump(
                    {'current_temperature_celsius': current_temperature_celsius}, f)
            message = summarize_temperature(
                config, current_temperature_celsius)
            print(f"DEBUG: {message}")
            if is_temperature_acceptable(config, current_temperature_celsius):
                GPIO.output(LED_PIN_RED, GPIO.LOW)
                GPIO.output(LED_PIN_GREEN, GPIO.HIGH)
                sleep(config['indicate_led_for_seconds'])
                GPIO.output(LED_PIN_GREEN, GPIO.LOW)
            else:
                push_notification(config, 'Problem', message, 4)
                GPIO.output(LED_PIN_GREEN, GPIO.LOW)
                GPIO.output(LED_PIN_RED, GPIO.HIGH)
                sleep(config['indicate_led_for_seconds'])
                GPIO.output(LED_PIN_RED, GPIO.LOW)
            sleep(config['read_temperature_after_seconds'])
    except Exception as e:
        print(e)
        end_time = timer()
        elapsed = end_time - start_time
        print(f"DEBUG: shutting down. Elapsed for {elapsed} seconds")
        GPIO.output(LED_PIN_GREEN, GPIO.LOW)
        GPIO.output(LED_PIN_RED, GPIO.LOW)
        GPIO.cleanup()


if __name__ == '__main__':
    start_time = timer()
    config = load_config()
    if config['start_message']:
        print(config['start_message'])

    Thread(target=monitor_forever, args=(config,)).start()
    if config['notify_temperature_every_seconds'] and config['notify_temperature_every_seconds'] > 0:
        Thread(target=periodic_status_report_forever, args=(config,)).start()
    else:
        print(f"DEBUG: update config.yml 'notify_temperature_every_seconds' to be > 0 if you want periodic notifications.")
