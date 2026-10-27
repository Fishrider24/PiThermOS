#!/bin/bash

echo "Starting TFT without XFCE..."

# Stop any previous Xorg
pkill Xorg 2>/dev/null
sleep 3

# Remove Xorg locks
rm -f /tmp/.X0-lock /tmp/.X11-unix/X0 2>/dev/null

# Start Xorg on the TFT
cd /usr/share/X11/xorg.conf.d
Xorg :0 -config 99-fbdev.conf &
XORG_PID=$!

# Give Xorg time to initialize
sleep 5

# Calibrate touchscreen

echo "Xorg TFT active."

# Start PiThermOS programs
cd /home/pi/PiThermOS
export DISPLAY=:0
echo "Starting thermostat control..."
/home/pi/PiThermOS/venv/bin/python3 thermostatcontrol.py &

echo "Starting web server..."
/home/pi/PiThermOS/venv/bin/python3 app.py &

echo "Starting UPS monitor..."
/home/pi/PiThermOS/venv/bin/python3 ups.py &

# Give PiThermOS and Xorg time to fully initialize
sleep 5

# Configure touchscreen
DISPLAY=:0 xinput set-prop "ADS7846 Touchscreen" \
"Coordinate Transformation Matrix" 0 -1 1 1 0 0 0 0 1
# Disable screen blanking and power management
DISPLAY=:0 xset s off
DISPLAY=:0 xset -dpms
DISPLAY=:0 xset s noblank

echo "Touchscreen configured."

echo "PiThermOS programs started."

# Keep the service running while Xorg is running
wait $XORG_PID
