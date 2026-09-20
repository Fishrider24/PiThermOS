
#!/usr/bin/python
import datetime
import threading
import os
import time
import logging
import sqlite3
import paho.mqtt.client as mqtt
from tempSensor import *
from control import *
from weather import *
from database import *
from tkinter import *
from tkinter import font
from influxdb import InfluxDBClient
import tracemalloc
import psutil
import subprocess
path = os.path.expanduser

# Change to True to enable logging, False to disable
logging = False


def influxdata():
    try:
        global skip
        if skip == 0:
            send_to_influxdb(measurement, location, influxtimestamp, temp_inside, hum_inside, setPoint, outtemperature, hum_local)
            skip = 1
#            print('skip')
            return
        else:
            skip = 0
#            print('notskip')
            return
    except:
        if logging:
            logging.warning('influxdata')
#		~~Set tKinter~~
root=Tk()
font.families()
root.configure(bg="black")
root.geometry("480x320")
root.attributes("-fullscreen", True)
root.bind("<F11>", lambda event: root.attributes("-fullscreen", not root.attributes("-fullscreen")))
root.wm_title("PiThermOS")

#		~~Setup Logging for Debugging~~
if logging:
    logging.basicConfig(
        format="{asctime} {levelname:<8} {message}",
        style='{',
        filename=path("~/PiThermOS/data/stat.log"),
        filemode='a'
    )
    logging.warning('test')

#		~~Path Variables~~
settings_path = path("~/PiThermOS/data/settings.db")
weather_path = path("~/PiThermOS/data/weather.db")
sensors_path = path("~/PiThermOS/data/sensors.db")
cool_path = path("~/PiThermOS/data/coolSet.txt")
hold_image_path = path("~/PiThermOS/static/images/hold.png")
hold_on_image_path = path("~/PiThermOS/static/images/hold_on.png")
hum_image_path = path("~/PiThermOS/static/images/hum.png")
hum_on_image_path = path("~/PiThermOS/static/images/hum_on.png")
heat_image_path = path("~/PiThermOS/static/images/heat.png")
heat_on_image_path = path("~/PiThermOS/static/images/heat_on.png")
heat_run_image_path = path("~/PiThermOS/static/images/heat_run.png")
cool_image_path = path("~/PiThermOS/static/images/ac.png")
cool_on_image_path = path("~/PiThermOS/static/images/ac_on.png")
cool_run_image_path = path("~/PiThermOS/static/images/ac_run.png")
fan_image_path = path("~/PiThermOS/static/images/fan.png")
fan_on_image_path = path("~/PiThermOS/static/images/fan_on.png")
ok_image_path = path("~/PiThermOS/static/images/ok.png")
#		~~Setup Databases~~
getDatabase()

# Logs the data to your InfluxDB
def send_to_influxdb(measurement, location, timestamp, temperature, humidity, setPoint, outtemperature, hum_local):
        try:
            payload = [
                 {"measurement": measurement,
                     "tags": {
                         "location": location,
                      },
                      "time": timestamp,
                      "fields": {
                          "temperature" : float("{:.1f}".format(temperature)),
                          "humidity": float("{:.1f}".format(humidity)),
                          "setPoint": setPoint,
                          "outtemperature": float("{:.1f}".format(outtemperature)),
                          "outhumidity": float("{:.1f}".format(hum_local))
                      }
                  }
                ]
            client.write_points(payload)
            return
        except:
            if logging:
                logging.warning('influx')

# Set up InfluxDB
influxIp, influxDatabase, influxUsername, influxPassword = getinfluxIp()

host = influxIp  # Set from Settings page on Webpage
port = 8086
username = influxUsername
password = influxPassword
db = influxDatabase
skip = 0
# InfluxDB client to write to
client = InfluxDBClient(host, port, username, password, db)

measurement = "indoor"  # Change this as necessary
location = "living_room"  # Change this as necessary
outmeasurement = "outside"  # Change this as necessary
weatherlocation = "outside"  # Change this as necessary

#		~~Setup MQTT~~
mqttUser, mqttPass = getMqtt()

mqtttherm = mqtt.Client("therm_mqtt") # Name Client
mqtttherm.username_pw_set(mqttUser, mqttPass)
mqtttherm.connect("localhost", 1883, keepalive=0) # Connect to local brokker


#		~~Variables~~
oneshotOn = "Off"
oneshotOff = "Off"
fan = 0
idle_timer = 0
heat_status = "Off"
cool_status = "Off"
cooling = 0
heating = 0
ac_timeout = "Off"
heat_timeout = "Off"
#		~~Check for Last Mode~~
heat_enabled = getHeatenable()
cool_enabled = getCoolenable()
fan_enabled = getFanenable()
#		~~Set Exit for Full Screen~~
def end_fullscreen(event):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))
    return
root.bind("<Escape>", end_fullscreen)

def wifi_toggle(event):
    os.system('sudo ifconfig wlan0 down')
    time.sleep(6)
    os.system('sudo ifconfig wlan0 up')
    return

#		~~Header Label~~
header_label_1 = Label(root, text="PiTherm  ", fg="Blue", bg="black", font="Quicksand 15")
header_label_1.grid(row=0,column=4,columnspan=3)
header_label_1.bind("<Button-1>", end_fullscreen)
header_label_2 = Label(root, text="OS", fg="Red", bg="black", anchor="n", font="Quicksand 15")
header_label_2.grid(row=0,column=6)


#		~~Column/Row Configure spacing~~
root.grid_columnconfigure(0, minsize=20)
root.grid_columnconfigure(1, minsize=30)
root.grid_columnconfigure(2, minsize=40)
root.grid_columnconfigure(3, minsize=40)
root.grid_columnconfigure(4, minsize=30)
root.grid_columnconfigure(5, minsize=40)
root.grid_columnconfigure(6, minsize=30)
root.grid_columnconfigure(7, minsize=40)
root.grid_columnconfigure(8, minsize=30)
root.grid_columnconfigure(9, minsize=30)
root.grid_columnconfigure(10, minsize=45)

#		~~Define Set Humidity Window~~
def sethumidityScreen():
        setHum = Toplevel()
        setHum.title("Set Humidity %")
        setHum.geometry("480x250")
        setHum.attributes("-fullscreen", True)
        setHum.configure(bg="black")
        header_label_1 = Label(setHum, text="Humidifier SetPoint", fg="Blue", bg="black", font="Quicksand 15")
        header_label_1.grid(row=0,column=3,columnspan=3)
        def up():
            upHum()
            hum = getHum()
            hum_label.config(text="{} %".format(hum))
            return
        def down():
            downHum()
            hum = getHum()
            hum_label.config(text="{} %".format(hum))
            return
        def exit():
            setHum.destroy()
            return
        hum = getHum()
        setHum.grid_columnconfigure(1, minsize=50)
        setHum.grid_columnconfigure(2, minsize=50)
        setHum.grid_columnconfigure(3, minsize=150)
        setHum.grid_columnconfigure(4, minsize=50)
        setHum.grid_columnconfigure(5, minsize=30)
        setHum.grid_rowconfigure(1, minsize=30)
        setHum.grid_rowconfigure(2, minsize=50)
        setHum.grid_rowconfigure(3, minsize=50)
        setHum.grid_rowconfigure(4, minsize=30)
        setHum.grid_rowconfigure(5, minsize=30)
        buttonup = Button(setHum, text=u'\u21e7', bg="Goldenrod", font="Times 15", command=up)
        buttonup.grid(row=2,column=5)
        hum_label = Label(setHum, text="{} %".format(hum), fg="Goldenrod", bg="black", font="Quicksand 40")
        hum_label.grid(row=2,column=3, rowspan=2)
        buttondown = Button(setHum, text=u'\u21e9', bg="Goldenrod", font="Times 15", command=down)
        buttondown.grid(row=3,column=5)
        okBtn_image = PhotoImage(file=ok_image_path)
        okBtn = Button(setHum, text="OK", bg="Goldenrod", font="Times 20", command=exit)
        okBtn.grid(row=6,column=3,columnspan=3)
        return

#		~~Define Reboot/wifi reset Window~~
def setrebootScreen(event):
        setReboot = Toplevel()
        setReboot.title("Settings")
        setReboot.geometry("480x250")
        setReboot.attributes("-fullscreen", True)
        setReboot.configure(bg="black")
        header_label_3 = Label(setReboot, text="Settings", fg="Blue", bg="black", font="Quicksand 15")
        header_label_3.grid(row=0,column=4,columnspan=3)
        def reboot():
            os.system('sudo reboot')
            return
        def wifireset():
            os.system('sudo ifconfig wlan0 down')
            time.sleep(6)
            os.system('sudo ifconfig wlan0 up')
            return
        def rebootexit():
            setReboot.destroy()
            return
        hum = getHum()
        setReboot.grid_columnconfigure(1, minsize=50)
        setReboot.grid_columnconfigure(2, minsize=50)
        setReboot.grid_columnconfigure(3, minsize=50)
        setReboot.grid_columnconfigure(4, minsize=50)
        setReboot.grid_columnconfigure(5, minsize=50)
        setReboot.grid_rowconfigure(1, minsize=30)
        setReboot.grid_rowconfigure(2, minsize=50)
        setReboot.grid_rowconfigure(3, minsize=50)
        setReboot.grid_rowconfigure(4, minsize=50)
        setReboot.grid_rowconfigure(5, minsize=50)
        buttonreboot = Button(setReboot, text="Reboot", bg="Goldenrod", font="Times 15", command=reboot)
        buttonreboot.grid(row=2,column=4,columnspan=3)
        buttonwifireset = Button(setReboot, text="Wifi_Reset", bg="Goldenrod", font="Times 15", command=wifireset)
        buttonwifireset.grid(row=3,column=4,columnspan=3)
        okBtn_image = PhotoImage(file=ok_image_path)
        okBtn = Button(setReboot, text="OK", bg="Goldenrod", font="Times 15", command=rebootexit)
        okBtn.grid(row=5,column=4,columnspan=3)
        return

setting_label_1 = Label(root, text="Settings", fg="Red", bg="black", anchor="n", font="Quicksand 10")
setting_label_1.grid(row=0,column=10)
setting_label_1.bind("<Button-1>", setrebootScreen)

def mqttOn():
    try:
        onHumrun()
        mqtttherm.publish("Hum","humon") # Turn on humidifier
        global oneshotOff, oneshotOn
        oneshotOn = "On"
        oneshotOff = "Off"
        return
    except:
        if logging:
            logging.warning('mqtton')

def mqttOff():
    try:
        offHumrun()
        mqtttherm.publish("Hum","humoff") # Turn off humidifier
        global oneshotOff, oneshotOn
        oneshotOff = "On"
        oneshotOn = "Off"
        return
    except:
        if logging:
            logging.warning('mqttoff')

#		~~Hum Button~~
hum_image = PhotoImage(file=hum_image_path)
hum_on_image = PhotoImage(file=hum_on_image_path)
hum_btn = Button(root, image=hum_image, bg="gray40", borderwidth="0", command=sethumidityScreen)
hum_btn.grid(row=2,column=8)

#		~~Date/Time Header~~
def time_thread():
    command=threading.Thread(target=time_get, daemon=True).start()
    return
def time_get():
    while True:
        try:
            hold = getHold()
            temp, hum = getInside()
            hum_set = getHum()
            date_now = datetime.datetime.now()
            date_now_str = date_now.strftime("%A %-I:%M %p")
            day_str = date_now.strftime("%A")
            second_str = date_now.strftime("%S")
            time_str = date_now.strftime("%-I:%M:%S %P")
            time_label.config(text=date_now_str)
            time.sleep(1)
            weekend = ("Saturday","Sunday")
            weekday = ("Monday","Tuesday","Wednesday","Thursday","Friday")
            if heating == "On":
                if hold == 1 and second_str == '00' and day_str in weekday:
                    getheatScheduleweekday()
                if hold == 1 and second_str == '00' and day_str in weekend:
                    getheatScheduleweekend()
                if hum <= (hum_set - 1) and heat_status == "On":
                    if oneshotOn == "Off":
                        mqttOn()
                if hum > hum_set and heat_status == "On":
                    if oneshotOff == "Off":
                        mqttOff()
                if heat_status == "Off" and oneshotOn == "On":
                    mqttOff()
            if cooling == "On":
                if hold == 1 and second_str == '00' and day_str in weekday:
                    getcoolScheduleweekday()
                if hold == 1 and second_str == '00' and day_str in weekend:
                    getcoolScheduleweekend()
        except:
            if logging:
                logging.warning('time_get')
#            print(exception)

time_label = Label(root, text=0, fg="Goldenrod", bg="black", font="Quicksand 18")
time_label.grid(row=1,column=3,columnspan=5)

#		~~Get Outside Weather~~
def weather_thread():
    command=threading.Thread(target=weather_get, daemon=True).start()
    return
def weather_get():
    while True:
        owmKey, owmCity, owmCountry = getowmKey()
        if owmKey != "0":
            try:
                global hum_local, temp_local, outtemperature
                temp_local, tempmax_local, hum_local, wind_local, feel_local = getWeather()
#		~~Current Weather Outside Title~~
                weather_label = Label(root, text="Current Weather Outside", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
                weather_label.grid(row=5,column=1,columnspan=4)
#		~~Feels Like Temp Outside Title~~
                weather_feels_label = Label(root, text="Feels Like", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
                weather_feels_label.grid(row=5,column=6,columnspan=2)
                weather_max_label = Label(root, text="Max Temp", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
                weather_max_label.grid(row=5,column=7,columnspan=3)
                temp_local_label = Label(root, text=temp_local, fg="Goldenrod", bg="black", font="Quicksand 15")
                temp_local_label.grid(row=6,column=1,columnspan=2)
                temp_local_label.config(text="{} \u02daF".format(temp_local))
                feel_local_label = Label(root, text=feel_local, fg="Goldenrod", bg="black", font="Quicksand 15")
                feel_local_label.grid(row=6,column=6,columnspan=2)
                feel_local_label.config(text="{} \u02daF".format(feel_local))
                tempmax_local_label = Label(root, text=tempmax_local, fg="Goldenrod", bg="black", font="Quicksand 15")
                tempmax_local_label.grid(row=6,column=7,columnspan=3)
                tempmax_local_label.config(text="{} \u02daF".format(tempmax_local))
                hum_local_label = Label(root, text=hum_local, fg="Goldenrod", bg="black", font="Quicksand 15")
                hum_local_label.grid(row=6,column=3,columnspan=1)
                hum_local_label.config(text="{} %".format(hum_local))
                wind_local_label = Label(root, text=wind_local, fg="Goldenrod", bg="black", font="Quicksand 15")
                wind_local_label.grid(row=6,column=4,columnspan=2)
                wind_local_label.config(text="{} mph".format(wind_local))
                outtemperature = float(temp_local)
            except:
                if logging:
                    logging.warning('weather_thread')
                print(exception)
                time.sleep(120)
            else:
                date_now = datetime.datetime.now()
                date_now_str = date_now.strftime("%A %-I:%M %p")
#		~~Last Update Outside Weather~~
                last_update_label = Label(root, text="Last Update", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
                last_update_label.grid(row=7,column=1,columnspan=2)
                update_label = Label(root, text=date_now_str, fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
                update_label.grid(row=7,column=3,columnspan=3)
                time.sleep(600)
        else:
            if 'temp_local_label' in locals():
                temp_local_label.grid_forget()
                tempmax_local_label.grid_forget()
                feel_local_label.grid_forget()
                hum_local_label.grid_forget()
                wind_local_label.grid_forget()
                weather_label.grid_forget()
                weather_feels_label.grid_forget()
                last_update_label.grid_forget()
                update_label.grid_forget()
                time.sleep(120)
            else:
                time.sleep(120)


#		~~Get Inside Temp~~
def sensor_thread():
    command=threading.Thread(target=sensor_get, daemon=True).start()
    return
def sensor_get():
    while True:
        try:
            if heat_status == "On":
                mqtttherm.publish("Alive","HeatKeepAlive") # If program closes, esp32 outputs shut off
                time.sleep(1)
                mqtttherm.publish("Alive","HumKeepAlive") # If program closes, esp32 outputs shut off
            sensor_call = getCurrent()
            global temp_inside, hum_inside, influxtimestamp
            temp_inside, hum_inside = getInside()
            temp_inside_label.config(text="{:.1f} \u02daF".format(temp_inside))
            hum_inside_label.config(text="{:.1f} %".format(hum_inside))
            influxtimestamp = datetime.datetime.utcnow()
            influxdata()
            time.sleep(10)
        except:
            if logging:
                logging.warning('sensor_get')
#            print(exception)

#		~~SetPoint UP~~
def up():
    upSetpoint()
    return

#		~~SetPoint DOWN~~
def down():
    downSetpoint()
    return

#		~~Update Hold~~
def hold():
    hold_value = getHold()
    if hold_value == 0:
        onHold()
        hold_btn.config(image=hold_image)
        return
    if hold_value == 1:
        offHold()
        hold_btn.config(image=hold_on_image)
        return

#		~~Temp Up Button~~
setpoint_up_btn = Button(root, text=u'\u21e7', bg="goldenrod", font="Quicksand 28", command=up)
setpoint_up_btn.grid(row=3,column=9,columnspan=2)

#		~~Temp Down Button~~
setpoint_down_btn = Button(root, text=u'\u21e9', bg="goldenrod", font="Quicksand 28", command=down)
setpoint_down_btn.grid(row=4,column=9,columnspan=2,rowspan=3)

#		~~Temp Hold Button~~
hold_image = PhotoImage(file=hold_image_path)
hold_on_image = PhotoImage(file=hold_on_image_path)
hold_btn = Button(root, image=hold_image, bg="gray40", borderwidth="0", command=hold)
hold_btn.grid(row=3,column=3,rowspan=2,columnspan=3)

#		~~Setpoint Label~~
setpoint_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 45")
setpoint_label.grid(row=3,column=5,rowspan=3,columnspan=4,padx=20)

#		~~Inside Temperature~~
temp_inside_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 27")
temp_inside_label.grid(row=3,column=0,columnspan=4)

#		~~Inside Humidity~~
hum_inside_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 27")
hum_inside_label.grid(row=4,column=0,columnspan=4)

#		~~Turn on from Fan Button~~
def fan_on():
    global fan, fanOn
    fan_value = getFan()
    if fan_value == 0:
        onFan()
        fan = 1
        fanOn = "On"
        fan_selected_thread()
        fan_btn.config(image=fan_on_image)
        return "On"
    if fan_value == 1:
        offFan()
        fan = 0
        fanOn = "Off"
        fan_btn.config(image=fan_image)
        return "Off"

#		~~Turn on Heat from button~~
def heat_on():
    try:
        global heating
        if cooling == "On":
            return
        else:
            heat_value = getHeat()
            if heat_value == 0:
                onHeat()
                heating = "On"
                heat_selected_thread()
                heat_btn.config(image=heat_on_image)
                return "On"
            if heat_value == 1:
                offHeat()
                mqttOff()
                heating = "Off"
                heat_btn.config(image=heat_image)
                return "Off"
    except:
        if logging:
            logging.warning('heat_on')

#		~~Turn on A/C from button~~
def cool_on():
    global cooling
    if heating == "On":
        return
    else:
       cool_value = getCool()
       if cool_value == 0:
            onCool()
            cooling = "On"
            cool_selected_thread()
            cool_btn.config(image=cool_on_image)
            return "On"
       if cool_value == 1:
            offCool()
            cooling = "Off"
            cool_btn.config(image=cool_image)
            return "Off"

#		~~Update Setpoint~~
def setpoint_thread():
    command=threading.Thread(target=setpoint_get, daemon=True).start()
    return 0
def setpoint_get():
    while True:
        try:
            global setPoint, heat_status, cool_status, idle_timer, heat_timeout, ac_timeout
            time.sleep(.5)
            heat_status, cool_status, idle_timer, heat_timeout, ac_timeout = getvariables()
            setPoint = float(getSetpoint())
            setpoint_label.config(text="{:.0f}\u02daF".format(setPoint))
            hold_value = getHold()
            if hold_value == 1:
                hold_btn.config(image=hold_image)
            if hold_value == 0:
                hold_btn.config(image=hold_on_image)
            fan = getFanenable()
            global fan_enabled
            if fan != fan_enabled:
                if fan == 0:
                    fan_enabled = 0
                    fan_on()
                if fan == 1:
                    fan_enabled = 1
                    fan_on()
            if oneshotOn == "On":
                hum_btn.config(image=hum_on_image)
            if oneshotOn == "Off":
                hum_btn.config(image=hum_image)
            heat = getHeatenable()
            global heat_enabled
            if heat != heat_enabled:
                if heat == 0:
                    heat_enabled = 0
                    heat_on()
                if heat == 1:
                    heat_enabled = 1
                    heat_on()
            cool = getCoolenable()
            global cool_enabled
            if cool != cool_enabled:
                if cool == 0:
                    cool_enabled = 0
                    cool_on()
                if cool == 1:
                    cool_enabled = 1
                    cool_on()
        except:
            if logging:
                logging.warning('threadset')
#            print(exception)

#		~~Heat Thread when Heat is Selected~~
def heat_selected_thread():
    command=threading.Thread(target=heat_selected, daemon=True).start()
    return 0
def heat_selected():
    while True:
        try:
            heatSwing, coolSwing = getSwing()
            swing = float(heatSwing)
            time.sleep(10)
            global heattimer
            if heating == "On":
                if temp_inside < (setPoint - swing) and heat_status == "Off" and idle_timer == 0 and heat_timeout == "Off":
                    heat()
                    onHeatrun()
                    mqtttherm.publish("Heat","heaton") # If program closes, esp32 outputs shut off
                    heat_btn.config(image=heat_run_image)
                if (temp_inside > (setPoint + swing) and heat_status == "On") or (heat_timeout == "On" and heat_status == "On"):
                    offHeatrun()
                    heat_btn.config(image=heat_on_image)
                    heat_power_down()
                    mqtttherm.publish("Heat","heatoff") # If program closes, esp32 outputs shut off
                    time.sleep(1)
                    mqttOff()
            if heating == "Off":
                if heat_status == "On":
                    offHeatrun()
                    heat_power_down()
                    mqtttherm.publish("Heat","heatoff") # If program closes, esp32 outputs shut off
                    mqttOff()
                    break
                else:
                    break
        except:
            if logging:
                logging.warning('heatmode')
#            print(exception)

#		~~A/C Thread when A/C is Selected~~
def cool_selected_thread():
    command=threading.Thread(target=cool_selected, daemon=True).start()
    return 0
def cool_selected():
    while True:
        try:
            heatSwing, coolSwing = getSwing()
            swing = float(coolSwing)
            time.sleep(10)
            if cooling == "On":
                if temp_inside > (setPoint + swing) and cool_status == "Off" and idle_timer == 0 and ac_timeout == "Off":
                    cool()
                    onCoolrun()
                    cool_btn.config(image=cool_run_image)
                if (temp_inside < (setPoint - swing) and cool_status == "On") or ac_timeout == "On":
                    offCoolrun()
                    cool_btn.config(image=cool_on_image)
                    cool_power_down()
            if cooling == "Off":
                if cool_status == "On":
                    offCoolrun()
                    cool_power_down()
                    break
                else:
                    break
        except:
            if logging:
                logging.warning('coolmode')
#            print(exception)

def fan_selected_thread():
    command=threading.Thread(target=fan_selected, daemon=True).start()
    return 0
def fan_selected():
    try:
        while True:
            time.sleep(1)
            if fanOn == "On":
                fanSet()
            if fanOn == "Off": # and coolOn == "Off" and heatOn == "Off":
                if cool_status == "On":
                    break
                fanOff()
    except:
        if logging:
            logging.warning('fan_selected')

#		~~Heat Button~~
heat_image = PhotoImage(file=heat_image_path)
heat_on_image = PhotoImage(file=heat_on_image_path)
heat_run_image = PhotoImage(file=heat_run_image_path)
heat_btn = Button(root, image=heat_image, bg="gray40", borderwidth="0", command=heat_on)
heat_btn.grid(row=2,column=2)

#		~~Check for Last Value of Heat Mode~~
def heat_check():
    heat_check_value = getHeat()
    if heat_check_value == 1:
        offHeat()
        offHeatrun()
        heat_on()
        return
    else:
        return

#		~~Check for Last Value of Cool Mode~~
def cool_check():
    cool_check_value = getCool()
    if cool_check_value == 1:
        offCool()
        offCoolrun()
        cool_on()
        return
    else:
        return

#		~~Check for Last Value of Fan Mode~~
def fan_check():
    fan_check_value = getFan()
    if fan_check_value == 1:
        offFan()
#        offCoolrun()
        fan_on()
        return
    else:
        return

#		~~A/C Button~~
cool_image = PhotoImage(file=cool_image_path)
cool_on_image = PhotoImage(file=cool_on_image_path)
cool_run_image = PhotoImage(file=cool_run_image_path)
cool_btn = Button(root, image=cool_image, bg="gray40", borderwidth="0", command=cool_on)
cool_btn.grid(row=2,column=4)

#		~~Fan Button~~
fan_image = PhotoImage(file=fan_image_path)
fan_on_image = PhotoImage(file=fan_on_image_path)
fan_btn = Button(root, image=fan_image, bg="gray40", borderwidth="0", command=fan_on)
fan_btn.grid(row=2,column=6)

#		~~Set Threads to start after window~~
root.after(1000, sensor_thread)
root.after(2000, setpoint_thread)
root.after(3000, time_thread)
root.after(4000, weather_thread)
heat_check()
cool_check()
fan_check()
root.mainloop()
GPIO.cleanup()
