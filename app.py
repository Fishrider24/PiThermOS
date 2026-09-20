from gevent import monkey; monkey.patch_all()
from flask import Flask, render_template, Response, stream_with_context, url_for, redirect, send_file, make_response, request
from gevent.pywsgi import WSGIServer
import datetime
import threading
import paho.mqtt.client as mqtt
import time
import json
import os
import matplotlib.pyplot as plt
import io
import sqlite3
from weather import *
from tempSensor import getCurrent
from database import *

path = os.path.expanduser

#		~Path Variables~
weather_path = path("~/PiThermOS/data/weather.db") #	~~Contains Tables:outtemp(temp),outwind(wind),outhum(hum) and outfeels(feels)
settings_path = path("~/PiThermOS/data/settings.db") # ~~Contains Tables:setPoint(setPoint), hold(hold), heatSet(heatSet), heat(heat), heatRun(heatRun), coolSet(coolSet), cool(cool), coolRun(coolRun), fanSet(fanSet)
sensors_path = path("~/PiThermOS/data/sensors.db") #
schedule_path = path("~/PiThermOS/data/schedule.db")
		#######################
app = Flask(__name__)
		#######################
##################

# Retrieve LAST data from database
def getLastData():
	try:
		conn=sqlite3.connect(sensors_path)
		curs=conn.cursor()
		for row in curs.execute("SELECT * FROM sensors ORDER BY timestamp DESC LIMIT 1"):
			time = str(row[0])
			temp = row[1]
			hum = row[2]
		curs.close()
		conn.close()
		return time, temp, hum
	except:
		return

def getHistData (numSamples):
	try:
		conn=sqlite3.connect(sensors_path)
		curs=conn.cursor()
		curs.execute("SELECT * FROM sensors ORDER BY timestamp DESC LIMIT "+str(numSamples))
		data = curs.fetchall()
		dates = []
		temps = []
		hums = []
		for row in reversed(data):
			dates.append(row[0])
			temps.append(row[1])
			hums.append(row[2])
		curs.close()
		conn.close()
		return dates, temps, hums
	except:
		return

def maxRowsTable():
	try:
		conn=sqlite3.connect(sensors_path)
		curs=conn.cursor()
		for row in curs.execute("select COUNT(temp) from  sensors"):
			maxNumberRows=row[0]
		curs.close()
		conn.close()
		return maxNumberRows
	except:
		return

# define and initialize global variables
global numSamples, getSamples
getSamples = 1
numSamples = maxRowsTable()
if (numSamples > 321):
	numSamples = 320

		##############################

@app.route("/graph")
def graph():
	try:
		time, temp, hum = getLastData()
		templateData = {
		  	'datetime'	: time,
			'temp'	: temp,
	      		'hum'	: hum,
	      		'numSamples'	: numSamples,
	      		'getSamples'	: getSamples
		}
		return render_template('graph.html', **templateData)
	except:
		return

		###############################3

@app.route('/graph', methods=['POST'])
def my_form_post():
	try:
		global numSamples, getSamples
		getSamples = int(request.form['numSamples'])
		numSamples = getSamples*320
		numMaxSamples = maxRowsTable()
		if (numSamples > numMaxSamples):
			numSamples = (numMaxSamples-1)
		time, temp, hum = getLastData()
		templateData = {
			'datetime'	: time,
			'temp'	: temp,
	      		'hum'	: hum,
			'numSamples' 	: numSamples,
	      		'getSamples'	: getSamples
		}
		return render_template('graph.html', **templateData)
	except:
		return

		###########################

@app.route('/plot/temp')
def plot_temp():
	try:
		times, temps, hums = getHistData(numSamples)
		hours = (numSamples/320)
		ys = temps
		axis = plt.subplot(1, 1, 1)
		axis.clear()
		axis.set_title("Temperature [°F]", fontsize=20)
		axis.set_xlabel("Samples", fontsize=20)
		axis.grid(True)
		xs2 = times
		xs = range(numSamples)
		axis.plot(xs, ys)
		output = io.BytesIO()
		plt.savefig(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	except:
		return

		##########################

@app.route('/plot/hum')
def plot_hum():
	try:
		times, temps, hums = getHistData(numSamples)
		ys = hums
		axis = plt.subplot(1, 1, 1)
		axis.clear()
		axis.set_title("Humidity [%]", fontsize=20)
		axis.set_xlabel("Samples", fontsize=20)
		axis.grid(True)
		xs = range(numSamples)
		axis.plot(xs, ys)
		output = io.BytesIO()
		plt.savefig(output)
		response = make_response(output.getvalue())
		response.mimetype = 'image/png'
		return response
	except:
		return

		#########################

@app.route('/')
def index():
	try:
		global hum, temp, time, setPoint, outSide
		time.sleep(1)
		outtemp, outtempmax, outwind, outhum, feelslike = getOutside()
		heaton = getHeat()
		heatrun = getHeatrun()
		owmKey, owmCity, owmCountry = getowmKey()
		custom_links = getCustomLinks()
		if owmKey == "0":
			onWeather = False
		else:
			onWeather = True
		if heaton == 1:
			if heatrun == 1:
				flame_image = ("/static/images/heat_run.png")
			else:
				flame_image = ("/static/images/heat_on.png")
		else:
			flame_image = ("/static/images/heat.png")
		coolon = getCool()
		coolrun = getCoolrun()
		if coolon == 1:
			if coolrun == 1:
				snow_image = ("/static/images/ac_run.png")
			else:
				snow_image = ("/static/images/ac_on.png")
		else:
			snow_image = ("/static/images/ac.png")
		holdon = getHold()
		if holdon == 1:
			hold_image = ("/static/images/hold.png")
		else:
			hold_image = ("/static/images/hold_on.png")
		fanon = getFan()
		if fanon == 1:
			fan_image = ("/static/images/fan_on.png")
		else:
			fan_image = ("/static/images/fan.png")
		humon = getHumrun()
		if humon == 1:
			hum_image = ("/static/images/hum_on.png")
		else:
			hum_image = ("/static/images/hum.png")
		now = datetime.datetime.now()
		timeString = now.strftime("%A %-I:%M %p")
		temp, hum = getInside()
		setPoint = getSetpoint()
		return render_template('index.html', feelslike=feelslike, outtemp=outtemp, outtempmax=outtempmax, outhum=outhum, outwind=outwind, temp=temp, hum_image=hum_image, flame_image=flame_image, snow_image=snow_image, hold_image=hold_image, fan_image=fan_image, time=timeString, hum=hum, setPoint=setPoint, onWeather=onWeather, custom_links=custom_links)
	except Exception as e:
    	print("INDEX ERROR:", e)
    	return str(e), 500

		#######################

@app.route("/increase/", methods=['POST'])
def increase():
	try:
		upSetpoint()
		return redirect(url_for('index'))
	except:
		return

@app.route("/decrease/", methods=['POST'])
def decrease():
	try:
		downSetpoint()
		return redirect(url_for('index'))
	except:
		return

		#######################

@app.route('/hum')
def hum():
	try:
		hum_setPoint = getHum()
		return render_template('hum.html', hum_setPoint=hum_setPoint)
	except:
		return

		#######################

@app.route("/hum_increase/", methods=['POST'])
def hum_increase():
	try:
		upHum()
		return redirect(url_for('hum'))
	except:
		return

@app.route("/hum_decrease/", methods=['POST'])
def hum_decrease():
	try:
		downHum()
		return redirect(url_for('hum'))
	except:
		return

		#########Heat Schedule##############

@app.route('/heatschedule')
def heatschedule():
	try:
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT * from heatschedule ORDER BY setDay, setAm, setHour")
		data = curs.fetchall()
		if data == None:
			time2 = data[0]
			temp2 = data[1]
		else:
			time2 = 0
			temp2 = 0
		conn.commit()
		curs.close()
		conn.close()
		return render_template('heatschedule.html', time2=time2, temp2=temp2, data=data)
	except:
		return

		#######################

@app.route('/heatschedule', methods=['POST'])
def my_heatschedule_post():
	try:
		global numSamples, getSamples
		day1 = request.form['day']
		hours1 = request.form['hours']
		minutes1 = request.form['minutes']
		ampm = request.form['am/pm']
		am1 = ampm.upper()
		temp1 = int (request.form['temp'])
		templateData = {
		  	'time'	: time,
			'temp'	: temp,
		}
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("INSERT INTO heatschedule (setHour, setMinute, setAm, setPoint, setDay) values (?, ?, ?, ?, ?)", (hours1, minutes1, am1, temp1, day1))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('heatschedule'))
	except:
		return

		########################

@app.route("/heatdelete/", methods=['POST'])
def heatdelete():
	try:
		id = request.form.get('id')
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("DELETE FROM heatschedule WHERE ID IN (?)", (id,))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('heatschedule'))
	except:
		return

		#########Cool Schedule##############

@app.route('/coolschedule')
def coolschedule():
	try:
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("SELECT * from coolschedule ORDER BY setDay, setAm, setHour")
		data = curs.fetchall()
		if data == None:
			time2 = data[0]
			temp2 = data[1]
		else:
			time2 = 0
			temp2 = 0
		conn.commit()
		curs.close()
		conn.close()
		return render_template('coolschedule.html', time2=time2, temp2=temp2, data=data)
	except:
		return

		#######################

@app.route('/coolschedule', methods=['POST'])
def my_coolschedule_post():
	try:
		global numSamples, getSamples
		day1 = request.form['day']
		hours1 = request.form['hours']
		minutes1 = request.form['minutes']
		ampm = request.form['am/pm']
		am1 = ampm.upper()
		temp1 = int (request.form['temp'])
		templateData = {
		  	'time'	: time,
			'temp'	: temp,
		}
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("INSERT INTO coolschedule (setHour, setMinute, setAm, setPoint, setDay) values (?, ?, ?, ?, ?)", (hours1, minutes1, am1, temp1, day1))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('coolschedule'))
	except:
		return

		########################

@app.route("/cooldelete/", methods=['POST'])
def cooldelete():
	try:
		id = request.form.get('id')
		conn=sqlite3.connect(schedule_path)
		curs=conn.cursor()
		curs.execute("DELETE FROM coolschedule WHERE ID IN (?)", (id,))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('coolschedule'))
	except:
		return

@app.route('/settings')
def settings():
	try:
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		for row in curs.execute("SELECT * FROM owmKey"):
			Key = row[1]
			City = (row[2])
			Country = row[3]
		for row in curs.execute("SELECT * FROM coolSwing"):
			swingcool = row[1]
		for row in curs.execute("SELECT * FROM heatSwing"):
			swingheat = row[1]
		for row in curs.execute("SELECT * FROM influxIp"):
			ipinflux = row[1]
			databaseinflux = row[2]
		curs.execute("SELECT id, name, url FROM customLinks ORDER BY id")
		custom_links = curs.fetchall()
		conn.commit()
		curs.close()
		conn.close()
		return render_template('settings.html', Key=Key, City=City, Country=Country, swingcool=swingcool, swingheat=swingheat, ipinflux=ipinflux, databaseinflux=databaseinflux, custom_links=custom_links)
	except:
		return

		#######################

@app.route('/add_link', methods=['POST'])
def add_link():
    try:
        name = request.form['linkName'].strip()
        url = request.form['linkUrl'].strip()
        if not name or not url:
            return redirect(url_for('settings'))
        # Only allow normal web links
        if not (url.startswith('http://') or url.startswith('https://')):
            return redirect(url_for('settings'))
        conn = sqlite3.connect(settings_path)
        curs = conn.cursor()
        curs.execute(
            "INSERT INTO customLinks (name, url) VALUES (?, ?)",
            (name, url)
        )
        conn.commit()
        curs.close()
        conn.close()
        return redirect(url_for('settings'))
    except:
        return redirect(url_for('settings'))

		#######################

@app.route('/delete_link', methods=['POST'])
def delete_link():
    try:
        link_id = request.form['id']
        conn = sqlite3.connect(settings_path)
        curs = conn.cursor()
        curs.execute(
            "DELETE FROM customLinks WHERE id = ?",
            (link_id,)
        )
        conn.commit()
        curs.close()
        conn.close()
        return redirect(url_for('settings'))
    except:
        return redirect(url_for('settings'))

		#######################

@app.route('/key_settings', methods=['POST'])
def owm_post():
	try:
		key = request.form['owmKey']
		city = request.form['owmCity']
		country = request.form['owmCountry']
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO owmKey (id, owmKey, owmCity, owmCountry) values (1, ?, ?, ?)", (key, city, country))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('settings'))
	except:
		return

		###########################

@app.route('/cool_settings', methods=['POST'])
def cool_swing_post():
	try:
		swing = request.form['coolSwing']
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO coolSwing (id, coolSwing) values (?, ?)", (1, swing))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('settings'))
	except:
		return

		###########################

@app.route('/heat_settings', methods=['POST'])
def heat_swing_post():
	try:
		swing = request.form['heatSwing']
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO heatSwing (id, heatSwing) values (?, ?)", (1, swing))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('settings'))
	except:
		return

		###########################

@app.route('/influx_settings', methods=['POST'])
def influxdb_post():
	try:
		ip = request.form['influxIp']
		database = request.form['influxDatabase']
		username = request.form['influxUsername']
		password = request.form['influxPassword']
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO influxIp (id, influxIp, influxDatabase, influxUsername, influxPassword) values (1, ?, ?, ?, ?)", (ip, database, username, password))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('settings'))
	except:
		return

		###########################

@app.route('/mqtt_settings', methods=['POST'])
def mqtt_post():
	try:
		username = request.form['mqttUsername']
		password = request.form['mqttPassword']
		conn=sqlite3.connect(settings_path)
		curs=conn.cursor()
		curs.execute("INSERT OR REPLACE INTO mqtt (id, mqttUser, mqttPass) values (1, ?, ?)", (username, password))
		conn.commit()
		curs.close()
		conn.close()
		return redirect(url_for('settings'))
	except:
		if logging:
			logging.warning('mqtt_post')
		return

		###########################

@app.route('/reboot_settings', methods=['POST'])
def reboot_post():
	try:
		reboot_start()
		return redirect(url_for('settings'))
	except:
		return

def reboot_start():
	command=threading.Thread(target=reboot, daemon=True).start()
	return
def reboot():
	while True:
		time.sleep(5)
		os.system('sudo reboot')

		###########################

@app.route("/heat/", methods=['POST'])
def heat():
	try:
		heat_value = getHeatenable()
		if heat_value == 0:
			onHeatenable()
			return redirect(url_for('index'))
		else:
			offHeatenable()
			return redirect(url_for('index'))
	except:
		return

		#######################

@app.route("/cool/", methods=['POST'])
def cool():
	try:
		cool_value = getCoolenable()
		if cool_value == 0:
			onCoolenable()
			return redirect(url_for('index'))
		else:
			offCoolenable()
			return redirect(url_for('index'))
	except:
		return

@app.route("/hold/", methods=['POST'])
def hold():
	try:
		hold_value = getHold()
		if hold_value == 0:
			onHold()
			return redirect(url_for('index'))
		else:
			offHold()
			return redirect(url_for('index'))
	except:
		return

		########################

@app.route("/fan/", methods=['POST'])
def fan():
	try:
		fan_value = getFanenable()
		if fan_value == 0:
			onFanenable()
			return redirect(url_for('index'))
		else:
			offFanenable()
			return redirect(url_for('index'))
	except:
		return

		########################

@app.route("/listen")
def listen():
	def respond():
		while True:
			try:
				time.sleep(2)
				now = datetime.datetime.now()
				timenow = now.strftime("%A %-I:%M %p")
				outtemp, outtempmax, outwind, outhum, feelslike = getOutside()
				heaton = getHeat()
				heatrun = getHeatrun()
				if heaton == 1:
					if heatrun == 1:
						flame_image = ("/static/images/heat_run.png")
					else:
						flame_image = ("/static/images/heat_on.png")
				else:
					flame_image = ("/static/images/heat.png")
				coolon = getCool()
				coolrun = getCoolrun()
				if coolon == 1:
					if coolrun == 1:
						snow_image = ("/static/images/ac_run.png")
					else:
						snow_image = ("/static/images/ac_on.png")
				else:
					snow_image = ("/static/images/ac.png")
				holdon = getHold()
				if holdon == 1:
					hold_image = ("/static/images/hold.png")
				else:
					hold_image = ("/static/images/hold_on.png")
				fanon = getFan()
				if fanon == 1:
					fan_image = ("/static/images/fan_on.png")
				else:
					fan_image = ("/static/images/fan.png")
				humon = getHumrun()
				if humon == 1:
					hum_image = ("/static/images/hum_on.png")
				else:
					hum_image = ("/static/images/hum.png")
				temp, hum = getInside()
				setPoint = getSetpoint()
				hum_setPoint = getHum()
				_data = json.dumps({"temp":temp, "time":timenow, "feelslike":feelslike, "outtemp":outtemp, "outtempmax":outtempmax, "outwind":outwind, "outhum":outhum, "hum":hum, "setPoint":setPoint, "hum_setPoint":hum_setPoint, "hum_image":hum_image, "flame_image":flame_image, "snow_image":snow_image, "hold_image":hold_image, "fan_image":fan_image})
				yield f"id: 1\ndata: {_data}\nevent: online\n\n"
			except:
				return
	return Response(respond(), mimetype='text/event-stream')

if __name__ == '__main__':
	http_server = WSGIServer(("0.0.0.0", 8080), app)
	http_server.serve_forever()