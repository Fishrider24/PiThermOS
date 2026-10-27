# PiThermOS -Upgraded-
## Pi Zero thermostat with touch screen, backup battery and auto restart. 
Updated for Bookworm Lite Legacy 64 bit with no desktop.  Moved some threads out of Tkinter that may have been an issue.

What I used: Raspberry Pi Zero2W, 3.5" 320x480 touchscreen, Pi Zero UPS Hat, BME280 humidity and temp board, esp-32S, G3MB-202P solid state relays.

Touchscreen and Webpage view.<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/touchscreen.png" width="200">

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermweb.PNG" width="200">

Settings page on webpage.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermsettings.PNG" width="200">&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermsettings2.PNG" width="200">

Separate Heat and A/C Schedules.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermheat.PNG" width="200">&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermac.PNG" width="200">

Humidifier setting.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermhum.PNG" width="200">

Bookworm(Legacy) lite 64 bit.  
Install the operating system with ssh access and user as pi.

1. sudo apt update then sudo apt upgrade
2. sudo raspi-config enable Spi, I2C and VNC in Interface Options and Disable Screen Blanking in Display Options.
3. sudo apt install git
4. cd /home/pi then git clone https://github.com/Fishrider24/PiThermOS.git
5. Create a Virtual Environment to run the program in.
cd /home/pi/PiThermOS then python3 -m venv --system-site-packages venv
6. Upgrade pip.
./venv/bin/python -m pip install --upgrade pip
7. Install Requirments.
./venv/bin/python -m pip install -r requirements.txt
8. Install touchscreen drivers.
sudo apt update
sudo apt install xserver-xorg xinit x11-xserver-utils xinput
sudo apt install xserver-xorg-video-fbdev xserver-xorg-input-evdev
9. Install the custom display overlay.
sudo cp ~/mpi3501-kernel-6.12-driver/mpi3501-custom.dtbo /boot/firmware/overlays/
10. Edit the boot configuration
sudo nano /boot/firmware/config.txt
Then add dtoverlay=mpi3501-custom and comment out #dtoverlay=vc4-kms-v3d
11. Create the service that runs the autostart script. sudo nano /etc/systemd/system/tft-desktop.service
12. Paste the following into tft-desktop.service 
[Unit]
Description=TFT Desktop
After=network.target

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
ExecStart=/home/pi/PiThermOS/start-tft-desktop-noxfce.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target

13. Save the file then run the following to activate it.
sudo systemctl daemon-reload
sudo systemctl enable tft-desktop.service
sudo systemctl start tft-desktop.service

14. ### Install Mosquitto mqtt broker, if your going to use MQTT.  
This is currently setup to turn on/off relay on a esp32 to turn on/off whole house humidifier.  mqtthum program is setup for turning on/off Heat, A/C and Fan also.    
sudo apt install -y mosquitto mosquitto-clients, sudo systemctl enable mosquitto.service  
To make password file, go to cd /etc/mosquitto, type sudo mosquitto_passwd -c pwfile.txt user, with user being the username you want. It will ask twice for the password you want.  
Edit this file, sudo nano /etc/mosquitto/mosquitto.conf  
At the bottom of the file add two lines, listener 1883 and allow_anonymous true(if not using password)  
If you want a password on Mqtt, set allow_anonymous false add password_file /etc/mosquitto/pwfile.txt to mosquitto.conf   

ESP32 NodeMCU-32S pins humPin = 23, heatPin =22, coolPin = 19, fanPin = 18. Heat, Cool and Fan not recommended due to router failure would stop your Furnace from working...  

If no monitor is connected, you can test by connecting over VNC, opening a terminal window. 
For the webserver go to your pi's ip address:8080 and see the Browser window.  

## License
PiThermOS original source code is released under the MIT License.

Copyright (c) 2026 Evan Potts

See the [LICENSE](LICENSE) file for the complete license text.

PiThermOS includes and uses third-party software and source code. Third-party
components remain under their respective licenses. The PiThermOS MIT License
does not replace or modify the licenses of third-party components.

### Python and Python Libraries

PiThermOS uses open-source software including:

- Python
- Flask
- gevent
- Paho MQTT Python Client
- Matplotlib
- SQLite
- smbus

Each component remains subject to its respective license.


## Third-Party Software and Credits

PiThermOS includes and uses third-party software and source code.
Third-party components remain under their respective licenses.

### Waveshare UPS / INA219 Code

PiThermOS includes a modified version of the INA219 Python code
originally provided by Waveshare as part of the Waveshare
UPS-Power-Module project.

Original source:
https://github.com/waveshare/UPS-Power-Module/blob/master/ups_display/ina219.py

Copyright (c) 2020 waveshare

The original Waveshare code is licensed under the MIT License.
The version included in PiThermOS has been modified for integration
with PiThermOS, including UPS battery monitoring and automatic
shutdown functionality.

The Waveshare MIT License and copyright notice are retained for
the portions derived from the original code.

### Random Nerd Tutorials

Parts of the PiThermOS ESP32 MQTT code are based on the
"ESP32 MQTT – Publish and Subscribe with Arduino IDE" tutorial
by Rui Santos / Random Nerd Tutorials.

Original source:
https://randomnerdtutorials.com/esp32-mqtt-publish-subscribe-arduino-ide/

The original code was modified substantially for use with PiThermOS,
including thermostat control, MQTT topics, GPIO assignments,
and other PiThermOS-specific functionality.

Original code is provided under the terms stated in the source
project. The original attribution and applicable license terms
are retained.
