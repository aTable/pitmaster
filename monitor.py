# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

from time import sleep
import board
import digitalio
import adafruit_max31855
import yaml
import io
import requests
import RPi.GPIO as GPIO
from timeit import default_timer as timer
import urllib3

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
    with open("config.yml", 'r') as raw_yml:
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
                config['temperature_minimum_fahrenheit'])

        if not config['temperature_minimum_celsius'] or not config['temperature_maximum_celsius']:
            print(f"missing required temperature range")
            exit(1)

        if not config['temperature_display_mode']:
            config['temperature_display_mode'] = 'celsius'

        return config


config = load_config()


def convert_fahrenheit_to_celsius(temperature):
    return (temperature - 32) * (5/9)


def convert_celsius_to_fahrenheit(temperature):
    return (temperature * 9/5) + 32


def read_current_temperature_celsius(max31855):
    tempC = max31855.temperature
    tempF = tempC * 9 / 5 + 32
    return tempC


def pretty_print_temperature(config, temperature_celsius):
    if config['temperature_display_mode'] == 'fahrenheit':
        return f"{str(convert_celsius_to_fahrenheit(temperature_celsius))}{degree_sign}F"
    else:
        return f"{str(temperature_celsius)}{degree_sign}C"


def push_notification(config, markdown_message):
    payload = {
        'topic': config['push_notification']['ntfy']['topic'],
        'priority': 4,
        'title': config['push_notification']['ntfy']['title'],
        'message': f"{markdown_message}"
    }
    for ntfy_server in config['push_notification']['ntfy']['servers']:
        res = requests.post(
            url=ntfy_server, headers={"Content-Type": "application/json"}, json=payload)
        if not res.ok:
            print(f"\tDEBUG: ntfy failure")
            print(f"\t{res.text}")


if __name__ == '__main__':
    start_time = timer()
    config = load_config()
    try:
        print(f"DEBUG: starting monitoring. All hail the pitmaster, may your beef be grain fed and your pork tender.")
        while True:
            current_temperature_celsius = read_current_temperature_celsius(
                max31855)
            if current_temperature_celsius >= config['temperature_minimum_celsius'] and current_temperature_celsius < config['temperature_maximum_celsius']:
                print(
                    f"\tDEBUG: current temp '{pretty_print_temperature(config, current_temperature_celsius)}' IS within allowed range {pretty_print_temperature(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature(config, config['temperature_maximum_celsius'])}")
                GPIO.output(LED_PIN_RED, GPIO.LOW)
                GPIO.output(LED_PIN_GREEN, GPIO.HIGH)
                sleep(config['indicate_led_for_seconds'])
                GPIO.output(LED_PIN_GREEN, GPIO.LOW)
            else:
                message = f"\tDEBUG: current temp '{pretty_print_temperature(config, current_temperature_celsius)}' is NOT within allowed range {pretty_print_temperature(config, config['temperature_minimum_celsius'])}-{pretty_print_temperature(config, config['temperature_maximum_celsius'])}"
                push_notification(config, message)
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
