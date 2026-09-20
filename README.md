# PiThermOS
## Pi Zero thermostat with touch screen, backup battery and auto restart. 
This is all very outdated libraries and OS. I've used it for 6 years with minor issues, but it has locked up before, with system not running, never locked up running.  Use at your own risk and please fork it and make it better.  I'm slowly trying to upgrade it.

What I used: Raspberry Pi Zero2W, 3.5" 320x480 touchscreen, Pi Zero UPS Hat, BME280 humidity and temp board, esp-32S, G3MB-202P solid state relays.

Touchscreen and Webpage view.<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/touchscreen.png" width="200">

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermweb.PNG" width="200">

Settings page on webpage.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermsettings.PNG" width="200">&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermsettings2.PNG" width="200">

Separate Heat and A/C Schedules.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermheat.PNG" width="200">&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermac.PNG" width="200">

Humidifier setting.

<img src="https://github.com/Fishrider24/PiThermOS/blob/main/screenshots/thermhum.PNG" width="200">

Bullseye(Legacy) with Raspberry Pi Desktop.  
Make swap file size bigger, so upgrade doesnt freeze. sudo dphys-swapfile swapoff then sudo nano /etc/dphys-swapfile  
Change size CONF_SWAPSIZE=1024 CTRL + X, followed by Y, then ENTER.  
sudo dphys-swapfile setup  
sudo dphys-swapfile swapon  
Update and upgrade raspbian.  
sudo apt update then sudo apt upgrade  
### Install Mosquitto mqtt broker, if your going to use MQTT.  
This is currently setup to turn on/off relay on a esp32 to turn on/off whole house humidifier.  mqtthum program is setup for turning on/off Heat, A/C and Fan also.    
sudo apt install -y mosquitto mosquitto-clients, sudo systemctl enable mosquitto.service  
To make password file, go to cd /etc/mosquitto, type sudo mosquitto_passwd -c pwfile.txt user, with user being the username you want. It will ask twice for the password you want.  
Edit this file, sudo nano /etc/mosquitto/mosquitto.conf  
At the bottom of the file add two lines, listener 1883 and allow_anonymous true(if not using password)  
If you want a password on Mqtt, set allow_anonymous false add password_file /etc/mosquitto/pwfile.txt to mosquitto.conf   
ESP32 NodeMCU-32S pins humPin = 23, heatPin =22, coolPin = 19, fanPin = 18. Heat, Cool and Fan not recommended due to router failure would stop your Furnace from working...  
### Clone Repository
cd /home/pi  
git clone https://github.com/Fishrider24/PiThermOS.git  
cd PiThermOS  
then pip3 install -r requirements.txt  
sudo apt-get install libatlas-base-dev  
run mv /home/pi/PiThermOS/autostart /home/pi/.config to add therm.desktop, web.desktop and ups.desktop.  
sudo raspi-config  
Enable Spi, I2C and VNC in Interface Options and Disable Screen Blanking in Display Options.  
cd /home/pi  
If using Goodtft 3.5" Touch screen do the following  
http://www.lcdwiki.com/3.5inch_RPi_Display  
If no monitor is connected, you can test by connecting over VNC, opening a terminal window. 
If the programs dont open, run python3 /PiThermOS/thermostatcontrol.py in a terminal window to see errors. Can do the same with python3 app.py in another terminal window.  
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
