#!/usr/bin/python
import datetime
import threading
import os
import time
import logging
import sqlite3
from tempSensor import *
from weather import *

path = os.path.expanduser

#               ~~Path Variables~~
settings_path = path("~/PiThermOS/data/settings.db") # ~~Contains Tables:setPoint(setPoint), hold(hold), heatSet(heatSet), heat(heat), heatRun(heatRun), coolSet(coolSet), cool(cool), coolRun(coolRun), fanSet(fanSet)
weather_path = path("~/PiThermOS/data/weather.db") # ~~Contains Tables:outtemp(temp),outwind(wind),outhum(hum) and outfeels(feels)
sensors_path = path("~/PiThermOS/data/sensors.db")
schedule_path = path("~/PiThermOS/data/schedule.db")

#               ~~Setup Databases~~
def getDatabase():
#			~~Write to settings.db~~
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("CREATE TABLE IF NOT EXISTS setPoint (id INTEGER PRIMARY KEY, setPoint NUMERIC)")
		curs.execute("SELECT setPoint from setPoint")
		setPoint_set=curs.fetchone()
		if setPoint_set == None:
			curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', '65')")
		curs.execute("CREATE TABLE IF NOT EXISTS owmKey (id INTEGER PRIMARY KEY, owmKey, owmCity, owmCountry)")
		curs.execute("SELECT owmKey from owmKey")
		owmKey_set=curs.fetchone()
		if owmKey_set == None:
			curs.execute("INSERT OR REPLACE INTO owmKey (id, owmKey, owmCity, owmCountry) values ('1', '0', 'Chicago', 'US')")
		curs.execute("CREATE TABLE IF NOT EXISTS hold (id INTEGER PRIMARY KEY, hold NUMERIC)")
		curs.execute("SELECT hold from hold")
		hold_set=curs.fetchone()
		if hold_set == None:
			curs.execute("INSERT OR REPLACE INTO hold (id, hold) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS heatSet (id INTEGER PRIMARY KEY, heatSet NUMERIC)")
		curs.execute("SELECT heatSet from heatSet")
		heatSet_set=curs.fetchone()
		if heatSet_set == None:
			curs.execute("INSERT OR REPLACE INTO heatSet (id, heatSet) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS heat (id INTEGER PRIMARY KEY, heat NUMERIC)")
		curs.execute("SELECT heat from heat")
		heat=curs.fetchone()
		if heat == None:
			curs.execute("INSERT OR REPLACE INTO heat (id, heat) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS heatRun (id INTEGER PRIMARY KEY, heatRun NUMERIC)")
		curs.execute("SELECT heatRun from heatRun")
		heatRun_set=curs.fetchone()
		if heatRun_set == None:
			curs.execute("INSERT OR REPLACE INTO heatRun (id, heatRun) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS coolSet (id INTEGER PRIMARY KEY, coolSet NUMERIC)")
		curs.execute("SELECT coolSet from coolSet")
		coolSet_set=curs.fetchone()
		if coolSet_set == None:
			curs.execute("INSERT OR REPLACE INTO coolSet (id, coolSet) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS cool (id INTEGER PRIMARY KEY, cool NUMERIC)")
		curs.execute("SELECT cool from cool")
		cool=curs.fetchone()
		if cool == None:
			curs.execute("INSERT OR REPLACE INTO cool (id, cool) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS coolRun (id INTEGER PRIMARY KEY, coolRun NUMERIC)")
		curs.execute("SELECT coolRun from coolRun")
		coolRun_set=curs.fetchone()
		if coolRun_set == None:
			curs.execute("INSERT OR REPLACE INTO coolRun (id, coolRun) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS fanSet (id INTEGER PRIMARY KEY, fanSet NUMERIC)")
		curs.execute("SELECT fanSet from fanSet")
		fanSet_set=curs.fetchone()
		if fanSet_set == None:
			curs.execute("INSERT OR REPLACE INTO fanSet (id, fanSet) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS fan (id INTEGER PRIMARY KEY, fan NUMERIC)")
		curs.execute("SELECT fan from fan")
		fan_set=curs.fetchone()
		if fan_set == None:
			curs.execute("INSERT OR REPLACE INTO fan (id, fan) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS hum (id INTEGER PRIMARY KEY, hum NUMERIC)")
		curs.execute("SELECT hum from hum")
		hum_set=curs.fetchone()
		if hum_set == None:
			curs.execute("INSERT OR REPLACE INTO hum (id, hum) values ('1', '35')")
		curs.execute("CREATE TABLE IF NOT EXISTS humRun (id INTEGER PRIMARY KEY, humRun NUMERIC)")
		curs.execute("SELECT humRun from humRun")
		humRun_set=curs.fetchone()
		if humRun_set == None:
			curs.execute("INSERT OR REPLACE INTO humRun (id, humRun) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS coolSwing (id INTEGER PRIMARY KEY, coolSwing)")
		curs.execute("SELECT coolSwing from coolSwing")
		coolSwing_set=curs.fetchone()
		if coolSwing_set == None:
			curs.execute("INSERT OR REPLACE INTO coolSwing (id, coolSwing) values ('1', '1')")
		curs.execute("CREATE TABLE IF NOT EXISTS heatSwing (id INTEGER PRIMARY KEY, heatSwing)")
		curs.execute("SELECT heatSwing from heatSwing")
		heatSwing_set=curs.fetchone()
		if heatSwing_set == None:
			curs.execute("INSERT OR REPLACE INTO heatSwing (id, heatSwing) values ('1', '1.2')")
		curs.execute("CREATE TABLE IF NOT EXISTS influxIp (id INTEGER PRIMARY KEY, influxIp, influxDatabase, influxUsername, influxPassword)")
		curs.execute("SELECT influxIp from influxIp")
		influxIp_set=curs.fetchone()
		if influxIp_set == None:
			curs.execute("INSERT OR REPLACE INTO influxIp (id, influxIp, influxDatabase, influxUsername, influxPassword) values ('1', '0', 'thermostat', 'admin', 'password')")
		curs.execute("CREATE TABLE IF NOT EXISTS mqtt (id INTEGER PRIMARY KEY, mqttUser, mqttPass)")
		curs.execute("SELECT mqttUser from mqtt")
		mqtt_set=curs.fetchone()
		if mqtt_set == None:
			curs.execute("INSERT OR REPLACE INTO mqtt (id, mqttUser, mqttPass) values ('1', 'admin', 'password')")
		curs.execute("CREATE TABLE IF NOT EXISTS customLinks (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, url TEXT NOT NULL)")
		conn.commit()
		curs.close()
		conn.close()

#			~~Write to schedule.db~~
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("CREATE TABLE IF NOT EXISTS heatschedule (ID INTEGER PRIMARY KEY AUTOINCREMENT, setHour NUMERIC, setMinute TEXT, setAm TEXT, setPoint NUMERIC, setDay TEXT)")
		curs.execute("CREATE TABLE IF NOT EXISTS coolschedule (ID INTEGER PRIMARY KEY AUTOINCREMENT, setHour NUMERIC, setMinute TEXT, setAm TEXT, setPoint NUMERIC, setDay TEXT)")
		conn.commit()
		curs.close()
		conn.close()
#			~~Write to weather.db~~
		conn=sqlite3.connect(weather_path)
		curs=conn.cursor()
		curs.execute("CREATE TABLE IF NOT EXISTS outtemp (id INTEGER PRIMARY KEY, temp NUMERIC DEFAULT (0))")
		curs.execute("SELECT temp from outtemp")
		outtemp_set=curs.fetchone()
		if outtemp_set == None:
			curs.execute("INSERT OR REPLACE INTO outtemp (id, temp) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS outtempmax (id INTEGER PRIMARY KEY, tempmax NUMERIC DEFAULT (0))")
		curs.execute("SELECT tempmax from outtempmax")
		outtempmax_set=curs.fetchone()
		if outtempmax_set == None:
			curs.execute("INSERT OR REPLACE INTO outtempmax (id, tempmax) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS outwind (id INTEGER PRIMARY KEY, wind NUMERIC DEFAULT (0))")
		curs.execute("SELECT wind from outwind")
		outwind_set=curs.fetchone()
		if outwind_set == None:
			curs.execute("INSERT OR REPLACE INTO outwind (id, wind) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS outhum (id INTEGER PRIMARY KEY, hum NUMERIC DEFAULT (0))")
		curs.execute("SELECT hum from outhum")
		outhum_set=curs.fetchone()
		if outhum_set == None:
			curs.execute("INSERT OR REPLACE INTO outhum (id, hum) values ('1', '0')")
		curs.execute("CREATE TABLE IF NOT EXISTS outfeels (id INTEGER PRIMARY KEY, feels NUMERIC DEFAULT (0))")
		curs.execute("SELECT feels from outfeels")
		outfeels_set=curs.fetchone()
		if outfeels_set == None:
			curs.execute("INSERT OR REPLACE INTO outfeels (id, feels) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()

		return
	except:
		return

#		~~Get Heat Weekday Schedule from Database~~
def getheatScheduleweekday():
	try:
		date_now = datetime.datetime.now()
		date_now_str = date_now.strftime("%A %-I:%M %p")
		day_str = date_now.strftime("%A")
		hour_str = date_now.strftime("%-I")
		minute_str = date_now.strftime("%M")
		ampm_str = date_now.strftime("%p")
		second_str = date_now.strftime("%S")
		day = 'Weekday'
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT setPoint from heatschedule WHERE setHour=? and setMinute=? and setAm=? and setDay=?", (hour_str, minute_str, ampm_str, day))
		data=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		if data == None:
			return
		else:
			conn=sqlite3.connect(settings_path)
			curs=conn.cursor()
			curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (data,))
			conn.commit()
			curs.close()
			conn.close()
			return
		return
	except:
		return

#		~~Get Heat Weekend Schedule from Database~~
def getheatScheduleweekend():
	try:
		date_now = datetime.datetime.now()
		date_now_str = date_now.strftime("%A %-I:%M %p")
		day_str = date_now.strftime("%A")
		hour_str = date_now.strftime("%-I")
		minute_str = date_now.strftime("%M")
		ampm_str = date_now.strftime("%p")
		second_str = date_now.strftime("%S")
#		day = 'weekDay'
		day = 'Weekend'
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT setPoint from heatschedule WHERE setHour=? and setMinute=? and setAm=? and setDay=?", (hour_str, minute_str, ampm_str, day))
		data=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		if data == None:
			return
		else:
			conn=sqlite3.connect(settings_path)
			curs=conn.cursor()
			curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (data,))
			conn.commit()
			curs.close()
			conn.close()
			return
		return
	except:
		return
#		~~Get Cool Weekday Schedule from Database~~
def getcoolScheduleweekday():
	try:
		date_now = datetime.datetime.now()
		date_now_str = date_now.strftime("%A %-I:%M %p")
		day_str = date_now.strftime("%A")
		hour_str = date_now.strftime("%-I")
		minute_str = date_now.strftime("%M")
		ampm_str = date_now.strftime("%p")
		second_str = date_now.strftime("%S")
		day = 'Weekday'
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT setPoint from coolschedule WHERE setHour=? and setMinute=? and setAm=? and setDay=?", (hour_str, minute_str, ampm_str, day))
		data=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		if data == None:
			return
		else:
			conn=sqlite3.connect(settings_path)
			curs=conn.cursor()
			curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (data,))
			conn.commit()
			curs.close()
			conn.close()
			return
		return
	except:
		return

#		~~Get Cool Weekend Schedule from Database~~
def getcoolScheduleweekend():
	try:
		date_now = datetime.datetime.now()
		date_now_str = date_now.strftime("%A %-I:%M %p")
		day_str = date_now.strftime("%A")
		hour_str = date_now.strftime("%-I")
		minute_str = date_now.strftime("%M")
		ampm_str = date_now.strftime("%p")
		second_str = date_now.strftime("%S")
#		day = 'weekDay'
		day = 'Weekend'
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT setPoint from coolschedule WHERE setHour=? and setMinute=? and setAm=? and setDay=?", (hour_str, minute_str, ampm_str, day))
		data=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		if data == None:
			return
		else:
			conn=sqlite3.connect(settings_path)
			curs=conn.cursor()
			curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (data,))
			conn.commit()
			curs.close()
			conn.close()
			return
		return
	except:
		return

#		~~Get Setpoint from Database~~
def getSetpoint():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT setPoint from setPoint")
		setPoint=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return setPoint
	except:
		return

#		~~Add 1 to Setpoint~~
def upSetpoint():
	try:
		setPoint = getSetpoint()
		add1 = int(setPoint) + 1
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (add1,))
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return
#		~~Subtract 1 from Setpoint~~
def downSetpoint():
	try:
		setPoint = getSetpoint()
		sub1 = int(setPoint) - 1
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO setPoint (id, setPoint) values ('1', ?)", (sub1,))
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get owmKey from Database~~
def getowmKey():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT * from owmKey")
		Key=curs.fetchone()
		owmKey=Key[1]
		owmCity=Key[2]
		owmCountry=Key[3]
		conn.commit()
		curs.close()
		conn.close()
		return owmKey, owmCity, owmCountry
	except:
		return

#		~~Get Swing from Database~~
def getSwing():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT heatSwing from heatSwing")
		heatSwing=curs.fetchone()[0]
		curs.execute("SELECT coolSwing from coolSwing")
		coolSwing=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return heatSwing, coolSwing
	except:
		return

def getinfluxIp():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT * from influxIp")
		influx=curs.fetchone()
		influxIp=influx[1]
		influxDatabase=influx[2]
		influxUsername=influx[3]
		influxPassword=influx[4]
		conn.commit()
		curs.close()
		conn.close()
		return influxIp, influxDatabase, influxUsername, influxPassword
	except:
		return

def getMqtt():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT * from mqtt")
		Mqtt=curs.fetchone()
		mqttUser=Mqtt[1]
		mqttPass=Mqtt[2]
		conn.commit()
		curs.close()
		conn.close()
		return mqttUser, mqttPass
	except:
		return

#		~~Get Hum% Value from Database~~
def getHum():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT hum from hum")
		hum=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return hum
	except:
		return

#		~~Add 1 to Hum% Value~~
def upHum():
	try:
		hum = getHum()
		add1 = int(hum) + 1
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO hum (id, hum) values ('1', ?)", (add1,))
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Sub 1 from Hum% Value~~
def downHum():
	try:
		hum = getHum()
		sub1 = int(hum) - 1
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO hum (id, hum) values ('1', ?)", (sub1,))
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Humrun Value from Database~~
def getHumrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT humRun from humRun")
		hum=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return hum
	except:
		return

#		~~Turn Humrun On~~
def onHumrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO humRun (id, humRun) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Humrun Off~~
def offHumrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO humRun (id, humRun) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Hold Value from Database~~
def getHold():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT hold from hold")
		hold=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return hold
	except:
		return
#		~~Turn Hold On~~
def onHold():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO hold (id, hold) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Hold Off~~
def offHold():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO hold (id, hold) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Heatset Value from Database~~
def getHeat():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT heatSet from heatSet")
		heat=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return heat
	except:
		return

#		~~Turn Heatset On~~
def onHeat():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heatSet (id, heatSet) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Heatset Off~~
def offHeat():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heatSet (id, heatSet) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Heatenable Value from Database~~
def getHeatenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT heat from heat")
		heat=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return heat
	except:
		return

#		~~Turn Heatenable On~~
def onHeatenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heat (id, heat) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Heatenable Off~~
def offHeatenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heat (id, heat) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Heatrun Value from Database~~
def getHeatrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT heatRun from heatRun")
		heat=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return heat
	except:
		return

#		~~Turn Heatrun On~~
def onHeatrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heatRun (id, heatRun) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Heatrun Off~~
def offHeatrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heatRun (id, heatRun) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Coolset Value from Database~~
def getCool():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT coolSet from coolSet")
		cool=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return cool
	except:
		return

#		~~Turn Coolset On~~
def onCool():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO coolSet (id, coolSet) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Coolset Off~~
def offCool():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO coolSet (id, coolSet) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#               ~~Get Coolenable Value from Database~~
def getCoolenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT cool from cool")
		cool=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return cool
	except:
		return

#               ~~Turn Coolenable On~~
def onCoolenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO cool (id, cool) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#               ~~Turn Coolenable Off~~
def offCoolenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO cool (id, cool) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#               ~~Get Coolrun Value from Database~~
def getCoolrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT coolRun from coolRun")
		cool=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return cool
	except:
		return

#               ~~Turn Coolrun On~~
def onCoolrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO coolRun (id, coolRun) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#               ~~Turn Coolrun Off~~
def offCoolrun():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO coolRun (id, coolRun) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Fan Value from Database~~
def getFan():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT fanSet from fanSet")
		fan=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return fan
	except:
		return

#		~~Turn Fan On~~
def onFan():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO fanSet (id, fanSet) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Fan Off~~
def offFan():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO fanSet (id, fanSet) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Fanenable Value from Database~~
def getFanenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT fan from fan")
		fan=curs.fetchone()[0]
		conn.commit()
		curs.close()
		conn.close()
		return fan
	except:
		return

#		~~Turn Fanenable On~~
def onFanenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO fan (id, fan) values ('1', '1')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Turn Fanenable Off~~
def offFanenable():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO fan (id, fan) values ('1', '0')")
		conn.commit()
		curs.close()
		conn.close()
		return
	except:
		return

#		~~Get Inside Temperature and Humidity~~
def getInside():
	try:
		conn=sqlite3.connect(sensors_path)
		curs=conn.cursor()
		curs.execute("SELECT * from sensors ORDER BY rowid DESC LIMIT 1")
		current=curs.fetchone()
		temp_inside=current[1]
		hum_inside=current[2]
		conn.commit()
		curs.close()
		conn.close()
		return temp_inside, hum_inside
	except:
		return

#		~~Get Outside Weather Data~~
def getOutside():
	try:
		conn=sqlite3.connect(weather_path)
		curs=conn.cursor()
		curs.execute("SELECT temp from outtemp")
		outtemp=curs.fetchone()[0]
		curs.execute("SELECT tempmax from outtempmax")
		outtempmax=curs.fetchone()[0]
		curs.execute("SELECT wind from outwind")
		outwind=curs.fetchone()[0]
		curs.execute("SELECT hum from outhum")
		outhum=curs.fetchone()[0]
		curs.execute("SELECT feels from outfeels")
		feelslike=curs.fetchone()[0]
		curs.close()
		conn.close()
		return outtemp, outtempmax, outwind, outhum, feelslike
	except:
		return

#		~~Get Custom Links~~
def getCustomLinks():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("SELECT name, url from customLinks Order By id")
		custom_links = curs.fetchall()
		curs.close()
		conn.close()
		return custom_links
	except:
		return