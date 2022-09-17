# pitmaster

## Hardware parts

| Item           | Purpose       |
| -------------- | ------------- |
| rpi 3 model B+ | mini computer |

## Guide

The MAX31855 ships like this

![img](docs/max31855-shipped.PNG)

Solder the pieces together to look like this (long legs downwards to fit into breadboard). Ignore the circuits above

![img](docs/max31855-soldered.PNG)

Put the MAX31855 anywhere into the breadboard, note that the actual location doesn't matter (within electrical circuit reason). If you want specifics, just follow this image.

![img](docs/target-circuit.png)

For beginners, note that the MAX31855 is inserted on the left half (ABCDE) and positioned not in column A as thats where the jumper cables connect.

Connect the GPIO to breadboard circuit like so

| GPIO         | MAX31855 breadboard |
| ------------ | ------------------- |
| 3.3V (#1)    | Vin                 |
| GND (#6)     | GND                 |
| MISO (#21)   | DO                  |
| GPIO 5 (#29) | CS                  |
| SCLK (#23)   | CLK                 |

Optionally, add your heatsink

![img](docs/heatsink.jpg)

Enable SPI on the pi (raspi-config //TODO: ansible task) and reboot

## Sources

- [adafruit unsupported guide for the pi GPIO headers](https://learn.adafruit.com/max31855-thermocouple-python-library/hardware)
- [adafruit ]
- [rpi 3 model B GPIO diagram](https://www.etechnophiles.com/raspberry-pi-3-b-pinout-with-gpio-functions-schematic-and-specs-in-detail/)
- [rpi 3 model B GPIO diagram](https://www.etechnophiles.com/wp-content/uploads/2020/12/HD-pinout-of-R-Pi-3-Model-B-GPIO-scaled.jpg)
- [rpi 3 model B GPIO diagram](https://pi4j.com/1.4/pins/rpi-3b.html)
- [rpi 3 model B GPIO diagram](https://pi4j.com/1.2/pins/model-3b-rev1.html)
- [rpi 3 model B GPIO diagram](https://community.element14.com/products/raspberry-pi/m/files/17428)
