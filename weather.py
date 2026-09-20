#!/usr/bin/python
from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps
from database import *
import os
import sqlite3
#import logging
path = os.path.expanduser

#		~~Setup Logging for Debugging~~
#logging.basicConfig(
#	format="{asctime} {levelname:<8} {message}",
#	style='{',
#	filename=path("~/PiThermOS/data/weatherlog.log"),
#	filemode='w'
#)
#logging.warning('weathertest')

weather_path = path("~/PiThermOS/data/weather.db") #	~~Contains Tables:outtemp(temp),outwind(wind),outhum(hum) and outfeels(feels)

		###################

def getWeather():
	while True:
		try:
			owmKey, owmCity, owmCountry = getowmKey()
			place = 'owmCity','owmCountry'
			global temp, currhum, windspeed, feelslike
			owm = OWM(owmKey)
			mgr = owm.weather_manager()
			observation = mgr.weather_at_place(owmCity)
			weather = observation.weather
			temp = weather.temperature(unit="fahrenheit")
			currhum = weather.humidity
			windspeed = weather.wind(unit="miles_hour")
			hum = currhum
			tempout = (temp["temp"])
			tempmax = (temp["temp_max"])
			tempmin = (temp["temp_min"])
			temp_format = str('{:.1f}'.format(tempout))
			tempmax_format = str('{:.1f}'.format(tempmax))
			wind = (windspeed["speed"])
			wind_format = str('{:.1f}'.format(wind))
			feelslike = (temp["feels_like"])
			feels_format = str('{:.1f}'.format(feelslike))
#			~~Write to weather.db~~
			conn=sqlite3.connect(weather_path)
			curs=conn.cursor()
			curs.execute("INSERT OR REPLACE INTO outtemp (id, temp) VALUES (1, ?)", (temp_format,))
			curs.execute("INSERT OR REPLACE INTO outtempmax (id, tempmax) VALUES (1, ?)", (tempmax_format,))
			curs.execute("INSERT OR REPLACE INTO outwind (id, wind) VALUES (1, ?)", (wind_format,))
			curs.execute("INSERT OR REPLACE INTO outhum  (id, hum) VALUES (1, ?)", (hum,))
			curs.execute("INSERT OR REPLACE INTO outfeels (id, feels) VALUES (1, ?)", (feels_format,))
			conn.commit()
			curs.close()
			conn.close()
			return temp_format, tempmax_format, hum, wind_format, feels_format
		except:
			time.sleep(900)

def getFandata():
    fan_value = getFan()
    return fan_value

