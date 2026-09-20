#!/usr/bin/python
#Based off the tutorial by adafruit here:
# http://learn.adafruit.com/adafruits-raspberry-pi-lesson-11-ds18b20-temperature-sensing/software
import sqlite3
import subprocess
import glob
import time
import bme280
import smbus2
import os

path = os.path.expanduser

#		~Path Variables~
sensors_path = path("~/PiThermOS/data/sensors.db")

port = 1
address = 0x76
bus = smbus2.SMBus(port)

def getCurrent():
	while True:
		try:
			global port, address, bus
			calibration_params = bme280.load_calibration_params(bus, address)
			data = bme280.sample(bus, address, calibration_params)
			humidity = data.humidity
			ambient_temp = data.temperature
			humid = "{:.1f}".format(humidity)
			celsius_format = "{:.2f}".format(ambient_temp)
			fahrenheit_convert = float(celsius_format) * 9.0 / 5.0 + 32
			fahrenheit_format = "{:.1f}".format(fahrenheit_convert)
			conn=sqlite3.connect(sensors_path)
			curs=conn.cursor()
			curs.execute("CREATE TABLE IF NOT EXISTS sensors (timestamp DATETIME, temp NUMERIC, hum NUMERIC)")
#	~~For Celsius comment out the next line and uncomment the line after~~
			curs.execute("INSERT INTO sensors values(datetime('now', 'localtime'), (?), (?))", (fahrenheit_format, humid))
#			curs.execute("INSERT INTO sensors values(datetime('now', 'localtime'), (?), (?))", (celsius_format, humid))
			curs.execute('SELECT COUNT(*) from sensors')
			curs_result = curs.fetchone()
			rows = curs_result[0]
			if rows >= 10640:
				curs.execute("DELETE FROM sensors WHERE timestamp < datetime('now') LIMIT 2000")
			conn.commit()
			curs.close()
			conn.close()
			time.sleep(1)
			return
		except:
			return
