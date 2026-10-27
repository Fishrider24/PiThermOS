
#!/usr/bin/python
import datetime
import threading
import os
import time
import logging
import sqlite3
try:
    import paho.mqtt.client as mqtt
except ImportError:
    mqtt = None
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
import queue

weather_queue = queue.Queue()
sensor_queue = queue.Queue()
setpoint_queue = queue.Queue()
heat_queue = queue.Queue()
cool_queue = queue.Queue()
path = os.path.expanduser

# Change to True to enable logging, False to disable
logging_enabled = False
# Outdoor weather values; None means no valid reading yet
outtemperature = None
hum_local = None

def influxdata():
    try:
        global skip
        if influxIp == '0' or not influxIp:
            return
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
        if logging_enabled:
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
if logging_enabled:
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
hold_image_path = path("~/PiThermOS/static/images/hold_tk.png")
hold_on_image_path = path("~/PiThermOS/static/images/hold_on.png")
hum_image_path = path("~/PiThermOS/static/images/hum_tk.png")
hum_on_image_path = path("~/PiThermOS/static/images/hum_on_tk.png")
heat_image_path = path("~/PiThermOS/static/images/heat.png")
heat_on_image_path = path("~/PiThermOS/static/images/heat_on.png")
heat_run_image_path = path("~/PiThermOS/static/images/heat_run.png")
cool_image_path = path("~/PiThermOS/static/images/ac.png")
cool_on_image_path = path("~/PiThermOS/static/images/ac_on.png")
cool_run_image_path = path("~/PiThermOS/static/images/ac_run.png")
fan_image_path = path("~/PiThermOS/static/images/fan_tk.png")
fan_on_image_path = path("~/PiThermOS/static/images/fan_on_tk.png")
ok_image_path = path("~/PiThermOS/static/images/ok.png")
#		~~Setup Databases~~
getDatabase()

# Logs the data to your InfluxDB
def send_to_influxdb(measurement, location, timestamp, temperature, humidity, setPoint, outtemperature, hum_local):
    try:
# Always send the indoor thermostat data
        fields = {
        "temperature": float("{:.1f}".format(temperature)),
        "humidity": float("{:.1f}".format(humidity)),
        "setPoint": setPoint
        }
    # Add outdoor weather data only when valid
        try:
            if outtemperature is not None:
                fields["outtemperature"] = float(outtemperature)
        except (TypeError, ValueError):
            pass
        try:
            if hum_local is not None:
                fields["outhumidity"] = float(hum_local)
        except (TypeError, ValueError):
            pass
        payload = [{
            "measurement": measurement,
            "tags": {
                "location": location
            },
            "time": timestamp,
            "fields": fields
        }]
        client.write_points(payload)
    except Exception as e:
        if logging_enabled:
            logging.warning("InfluxDB write failed: %s", e)

# Set up InfluxDB
influxIp, influxDatabase, influxUsername, influxPassword = getinfluxIp()
host = influxIp  # Set from Settings page on Webpage
port = 8086
username = influxUsername
password = influxPassword
db = influxDatabase
skip = 0
# InfluxDB client to write to
client = None
if influxIp != '0' and influxIp:
    client = InfluxDBClient(host, port, username, password, db)

measurement = "indoor"  # Change this as necessary
location = "living_room"  # Change this as necessary
outmeasurement = "outside"  # Change this as necessary
weatherlocation = "outside"  # Change this as necessary

#		~~Setup MQTT~~
mqtttherm = None

if mqtt is not None:
    try:
        mqttUser, mqttPass, mqttHost, mqttPort = getMqtt()
        mqtttherm = mqtt.Client("therm_mqtt")
        mqtttherm.username_pw_set(mqttUser, mqttPass)
        mqtttherm.connect(mqttHost, int(mqttPort), keepalive=60)
        mqtttherm.loop_start()
    except Exception as e:
        mqtttherm = None
        if logging_enabled:
            logging.warning("MQTT unavailable: %s", e)

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
sensor_fault = False
padding = 20
#		~~Check for Last Mode~~
heat_enabled = getHeatenable()
cool_enabled = getCoolenable()
fan_enabled = getFanenable()
humidifier = getHumidifier()
#		~~Set Exit for Full Screen~~
def end_fullscreen(event):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))
    return
root.bind("<Escape>", end_fullscreen)

def wifi_toggle(event):
    os.system('sudo nmcli device connect wlan0')
    return

# 		~~Header Frame~~
header_frame = Frame(root, bg="black")
header_frame.grid(row=0, column=0, columnspan=9, padx=(20, 0))

# 		~~Header Labels~~
header_label_1 = Label(
    header_frame, text="PiTherm",
    fg="Blue", bg="black", font="Quicksand 20"
)
header_label_1.pack(side=LEFT)
header_label_1.bind("<Button-1>", end_fullscreen)
header_label_2 = Label(
    header_frame, text="OS",
    fg="Red", bg="black", font="Quicksand 20"
)
header_label_2.pack(side=LEFT)


#		~~Column/Row Configure spacing~~
#for col in range(11):
#    root.grid_columnconfigure(col, minsize=0, weight=1)
root.grid_columnconfigure(0, minsize=48)
root.grid_columnconfigure(1, minsize=48)
root.grid_columnconfigure(2, minsize=48)
root.grid_columnconfigure(3, minsize=48)
root.grid_columnconfigure(4, minsize=48)
root.grid_columnconfigure(5, minsize=48)
root.grid_columnconfigure(6, minsize=48)
root.grid_columnconfigure(7, minsize=48)
root.grid_columnconfigure(8, minsize=48)
root.grid_columnconfigure(9, minsize=48)
root.grid_columnconfigure(10, minsize=48)

#		~~Define Set Humidity Window~~
def sethumidityScreen():
        setHum = Toplevel()
        setHum.title("Set Humidity %")
        setHum.geometry("480x320")
        setHum.attributes("-fullscreen", True)
        setHum.configure(bg="black")
        header_label_1 = Label(setHum, text="Humidifier SetPoint", fg="Blue", bg="black", font="Quicksand 15")
        header_label_1.grid(row=0,column=3,columnspan=3)
        def up():
            upHum()
            hum = getHum()
            root.after(0, lambda h=hum: hum_label.config(text="{} %".format(h)))
            return
        def down():
            downHum()
            hum = getHum()
            root.after(0, lambda h=hum: hum_label.config(text="{} %".format(h)))
            return
        def toggleHumidifier():
            humidifier = getHumidifier()
            if humidifier == 1:
                offHumidifier()
            else:
                onHumidifier()
            updateHumidifierButton()
        def updateHumidifierButton():
            humidifier = getHumidifier()
            if humidifier == 1:
                humidifier_button.config(text="Humidifier Enabled")
            else:
                humidifier_button.config(text="Humidifier Disabled")
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
        humidifier_button = Button(setHum, text="", bg="Goldenrod", font="Times 14", command=toggleHumidifier)
        humidifier_button.grid(row=6, column=3, columnspan=3)
        updateHumidifierButton()
        okBtn = Button(setHum, text="OK", bg="Goldenrod", font="Times 20", command=exit)
        okBtn.grid(row=4,column=3,columnspan=3)
        return

#		~~Define Reboot/wifi reset Window~~
def setrebootScreen(event):
        setReboot = Toplevel()
        setReboot.title("Settings")
        setReboot.geometry("480x320")
        setReboot.attributes("-fullscreen", True)
        setReboot.configure(bg="black")
        header_label_3 = Label(setReboot, text="Settings", fg="Blue", bg="black", font="Quicksand 15")
        header_label_3.grid(row=0,column=4,columnspan=3)
        def reboot():
            os.system('sudo /usr/bin/systemctl reboot')
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
#        okBtn_image = PhotoImage(file=ok_image_path)
        okBtn = Button(setReboot, text="OK", bg="Goldenrod", font="Times 15", command=rebootexit)
        okBtn.grid(row=4,column=4,columnspan=3)
        return
#               ~~Frame for Buttons~~
button_frame = Frame(root, bg="black")
button_frame.grid(row=2, column=0, columnspan=10, sticky="w", padx=(8, 0))

#               ~~Settings Button~~
settings_image = PhotoImage(file=path("~/PiThermOS/static/images/settings_tk.png"))
settings_btn = Button(button_frame, image=settings_image, bg="black", borderwidth="0", highlightbackground="black", command=lambda: setrebootScreen(None))
settings_btn.grid(row=2, column=8, padx=padding)

def mqttOn():
    try:
        onHumrun()
        if mqtttherm is not None:
            mqtttherm.publish("Hum", "humon") # Turn on humidifier
        global oneshotOff, oneshotOn
        oneshotOn = "On"
        oneshotOff = "Off"
        return
    except:
        if logging_enabled:
            logging.warning('mqtton')

def mqttOff():
    try:
        offHumrun()
        if mqtttherm is not None:
            mqtttherm.publish("Hum", "humoff") # Turn off humidifier
        global oneshotOff, oneshotOn
        oneshotOff = "On"
        oneshotOn = "Off"
        return
    except:
        if logging_enabled:
            logging.warning('mqttoff')

#		~~Hum Button~~
hum_image = PhotoImage(file=hum_image_path)
hum_on_image = PhotoImage(file=hum_on_image_path)
hum_btn = Button(button_frame, image=hum_image, bg="black", borderwidth="0", highlightbackground="black", command=sethumidityScreen)
hum_btn.grid(row=2,column=6,padx=padding)

#		~~Date/Time Header~~
def time_thread():
    command=threading.Thread(target=time_get, daemon=True).start()
    return
def time_get():
    last_schedule_minute = None
    while True:
        try:
            hold = getHold()
            temp, hum = getInside()
            hum_set = getHum()
            humidifier = getHumidifier()
            date_now = datetime.datetime.now()
            date_now_str = date_now.strftime("%A %-I:%M %p")
            day_str = date_now.strftime("%A")
            second_str = date_now.strftime("%S")
            time_str = date_now.strftime("%-I:%M:%S %P")
            root.after(0, lambda: time_label.config(text=date_now_str))
            time.sleep(1)
            weekend = ("Saturday","Sunday")
            weekday = ("Monday","Tuesday","Wednesday","Thursday","Friday")
            schedule_minute = date_now.strftime("%Y-%m-%d %H:%M")
            if schedule_minute != last_schedule_minute:
                last_schedule_minute = schedule_minute
                if hold == 1:
                    if heating == "On":
                        if day_str in weekday:
                            getheatScheduleweekday()
                        elif day_str in weekend:
                            getheatScheduleweekend()
                    if cooling == "On":
                        if day_str in weekday:
                            getcoolScheduleweekday()
                        elif day_str in weekend:
                            getcoolScheduleweekend()
            if humidifier == 1:
                if hum <= (hum_set - 1) and heat_status == "On":
                    if oneshotOn == "Off":
                        mqttOn()
                if hum > hum_set and heat_status == "On":
                    if oneshotOff == "Off":
                        mqttOff()
                if heat_status == "Off" and oneshotOn == "On":
                    mqttOff()
            if humidifier == 0 and oneshotOn == "On":
                mqttOff()
        except:
            if logging_enabled:
                logging.warning('time_get')
#            print(exception)

# 		~~Time Frame~~
time_frame = Frame(root, bg="black")
time_frame.grid(row=1, column=0, columnspan=9, padx=(20, 0))

time_label = Label(time_frame, text=  0, fg="Goldenrod", bg="black", font="Quicksand 14")
time_label.grid(row=1,column=2,columnspan=3)


def hide_weather_display():
    print("DEBUG: hide_weather_display called")
    labels = (
        'temp_local_label',
        'feel_local_label',
        'hum_local_label',
        'wind_local_label',
        'weather_label',
        'weather_feels_label',
        'last_update_label',
        'update_label'
    )
    for name in labels:
        label = globals().get(name)
        if label is not None:
            label.config(text="")
            label.grid_forget()

def update_weather_display(temp_local, hum_local, wind_local, feel_local, date_now_str):
    global weather_label, weather_feels_label
    global temp_local_label, feel_local_label
    global hum_local_label, wind_local_label, last_update_label, update_label

    weather_label = Label(root, text="Current Weather Outside", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
    weather_label.grid(row=6, column=0, columnspan=4)

    weather_feels_label = Label(root, text="Feels Like", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
    weather_feels_label.grid(row=6, column=4, columnspan=2)

    temp_unit = getTempUnit()
    temp_local_label = Label(root, text="{} \u02da{}".format(temp_local, temp_unit), fg="Goldenrod", bg="black", font="Quicksand 15")
    temp_local_label.grid(row=7, column=0, columnspan=1)

    feel_local_label = Label(root, text="{} \u02da{}".format(feel_local, getTempUnit()), fg="Goldenrod", bg="black", font="Quicksand 15")
    feel_local_label.grid(row=7, column=4, columnspan=2)

    hum_local_label = Label(root, text="  {} %".format(hum_local), fg="Goldenrod", bg="black", font="Quicksand 15")
    hum_local_label.grid(row=7, column=1, columnspan=1)

    wind_local_label = Label(root, text="{} mph".format(wind_local), fg="Goldenrod", bg="black", font="Quicksand 15")
    wind_local_label.grid(row=7, column=2, columnspan=2)

    last_update_label = Label(root, text="Last Update:", fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
    last_update_label.grid(row=9, column=0, columnspan=2)

    update_label = Label(root, text=date_now_str, fg="DeepSkyBlue2", bg="black", font="Quicksand 10")
    update_label.grid(row=9, column=2, columnspan=2)

def check_weather_queue():
    try:
        while True:
            weather_data = weather_queue.get_nowait()

            if weather_data[0] == "update":
                update_weather_display(*weather_data[1:])
            elif weather_data[0] == "hide":
                hide_weather_display()

    except queue.Empty:
        pass
    root.after(200, check_weather_queue)

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
                temp_local, hum_local, wind_local, feel_local = getWeather()
                outtemperature = float(temp_local)
            except Exception as e:
                if logging_enabled:
                    print("Weather thread error:", e)
                time.sleep(120)
            else:
                date_now = datetime.datetime.now()
                date_now_str = date_now.strftime("%A %-I:%M %p")
                weather_queue.put(("update", temp_local, hum_local, wind_local, feel_local, date_now_str))
#		~~Last Update Outside Weather~~
                time.sleep(600)
        else:
            weather_queue.put(("hide",))
            time.sleep(120)

def check_sensor_queue():
    try:
        while True:
            sensor_data = sensor_queue.get_nowait()
            temp_unit = getTempUnit()
            temp_inside_label.config(text="{:.1f} ˚{}".format(sensor_data[0], temp_unit))
            hum_inside_label.config(text="{:.1f} %".format(sensor_data[1]))
    except queue.Empty:
        pass

    root.after(200, check_sensor_queue)
#		~~Get Inside Temp~~
def sensor_thread():
    command=threading.Thread(target=sensor_get, daemon=True).start()
    return
def sensor_get():
    while True:
        try:
            if heat_status == "On":
                if mqtttherm is not None:
                    mqtttherm.publish("Alive","HeatKeepAlive") # If program closes, esp32 outputs shut off
                    time.sleep(1)
                    mqtttherm.publish("Alive","HumKeepAlive") # If program closes, esp32 outputs shut off
            sensor_call = getCurrent()
            if sensor_call == False:
                global sensor_fault
                sensor_fault = True
                if logging_enabled:
                    logging.warning('BME280 sensor read failed')
                time.sleep(1)
                continue
            if not sensor_reading_fresh():
                sensor_fault = True
                if logging_enabled:
                    logging.warning('BME280 sensor reading is stale')
                time.sleep(1)
                continue
#           else:
#                if heat_status == "Off" and cool_status == "Off":
#                    sensor_fault = False
            global temp_inside, hum_inside, influxtimestamp
            inside_data = getInside()
            if inside_data is None:
                sensor_fault = True
                if logging_enabled:
                    logging.warning('Unable to retrieve inside sensor data')
                time.sleep(1)
                continue
            temp_inside, hum_inside = inside_data
            try:
                temp_inside = float(temp_inside)
                hum_inside = float(hum_inside)
            except (TypeError, ValueError):
                sensor_fault = True
                if logging_enabled:
                    logging.warning('Invalid inside sensor data')
                time.sleep(1)
                continue
            if sensor_fault and heat_status == "Off" and cool_status == "Off":
                sensor_fault = False
                if logging_enabled:
                    logging.info('BME280 sensor recovered')
            sensor_queue.put((temp_inside, hum_inside))            
            influxtimestamp = datetime.datetime.utcnow()
            influxdata()
            time.sleep(10)
        except:
            sensor_fault = True
            if logging_enabled:
                logging.warning('sensor_get')
            time.sleep(1)
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
setpoint_up_btn.grid(row=3,column=7,columnspan=2,rowspan=2)

#		~~Temp Down Button~~
setpoint_down_btn = Button(root, text=u'\u21e9', bg="goldenrod", font="Quicksand 28", command=down)
setpoint_down_btn.grid(row=5,column=7,columnspan=2,rowspan=3)

#		~~Temp Hold Button~~
hold_image = PhotoImage(file=hold_image_path)
hold_on_image = PhotoImage(file=hold_on_image_path)
hold_btn = Button(root, image=hold_image, bg="black", borderwidth="0", highlightbackground="black", command=hold)
hold_btn.grid(row=3,column=2,rowspan=2,columnspan=3)

#		~~Setpoint Title Label~~
setpoint_title_label = Label(root, text="Setpoint", fg="DeepSkyBlue2", bg="black", font="Quicksand 14")
setpoint_title_label.grid(row=3,column=4,rowspan=1,columnspan=3,sticky="s",padx=20)

#		~~Setpoint Label~~
setpoint_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 45")
setpoint_label.grid(row=4,column=4,rowspan=2,columnspan=3,padx=20)

#		~~Inside Temperature~~
temp_inside_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 27")
temp_inside_label.grid(row=3,column=0,columnspan=3)

#		~~Inside Humidity~~
hum_inside_label = Label(root, text="0", fg="Goldenrod", bg="black", font="Quicksand 27")
hum_inside_label.grid(row=4,column=0,columnspan=3)

#		~~Turn on from Fan Button~~
def fan_on():
    global fan, fanOn
    fan_value = getFan()
    if fan_value == 0:
        onFan()
        fan = 1
        fanOn = "On"
        fan_selected_thread()
        root.after(0, lambda: fan_btn.config(image=fan_on_image))
        return "On"
    if fan_value == 1:
        offFan()
        fan = 0
        fanOn = "Off"
        root.after(0, lambda: fan_btn.config(image=fan_image))
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
                root.after(0, lambda: heat_btn.config(image=heat_on_image))
                return "On"
            if heat_value == 1:
                offHeat()
                mqttOff()
                heating = "Off"
                root.after(0, lambda: heat_btn.config(image=heat_image))
                return "Off"
    except:
        if logging_enabled:
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
            root.after(0, lambda: cool_btn.config(image=cool_on_image))
            return "On"
       if cool_value == 1:
            offCool()
            cooling = "Off"
            root.after(0, lambda: cool_btn.config(image=cool_image))
            return "Off"

def check_setpoint_queue():
    try:
        while True:
            setpoint_data = setpoint_queue.get_nowait()
            setPoint_value, hold_value, oneshot_value = setpoint_data

            temp_unit = getTempUnit()
            setpoint_format = "{:.1f}" if temp_unit == "C" else "{:.0f}"
            setpoint_font = 30 if temp_unit == "C" else 35
            setpoint_label.config(
                text="{}˚{}".format(setpoint_format.format(setPoint_value), temp_unit), font=("Quicksand", setpoint_font))
            if hold_value == 1:
                hold_btn.config(image=hold_image)
            if hold_value == 0:
                hold_btn.config(image=hold_on_image)

            if oneshot_value == "On":
                hum_btn.config(image=hum_on_image)
            if oneshot_value == "Off":
                hum_btn.config(image=hum_image)

    except queue.Empty:
        pass

    root.after(200, check_setpoint_queue)
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
            hold_value = getHold()
            setpoint_queue.put((setPoint, hold_value, oneshotOn))
            fan = getFanenable()
            global fan_enabled
            if fan != fan_enabled:
                if fan == 0:
                    fan_enabled = 0
                    fan_on()
                if fan == 1:
                    fan_enabled = 1
                    fan_on()
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
            if logging_enabled:
                logging.warning('threadset')
            time.sleep(1)
#            print(exception)

def check_heat_queue():
    try:
        while True:
            heat_image = heat_queue.get_nowait()
            heat_btn.config(image=heat_image)
    except queue.Empty:
        pass

    root.after(200, check_heat_queue)
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
            if sensor_fault:
                if heat_status == "On":
                    offHeatrun()
                    heat_queue.put(heat_on_image)
                    heat_power_down()
                    if mqtttherm is not None:
                        mqtttherm.publish("Heat", "heatoff")
                    mqttOff()
                time.sleep(1)
                continue
            if heating == "On":
                if temp_inside < (setPoint - swing) and heat_status == "Off" and idle_timer == 0 and heat_timeout == "Off":
                    heat()
                    onHeatrun()
                    if mqtttherm is not None:
                        mqtttherm.publish("Heat","heaton") # If program closes, esp32 outputs shut off
                    heat_queue.put(heat_run_image)
                if (temp_inside > (setPoint + swing) and heat_status == "On") or (heat_timeout == "On" and heat_status == "On"):
                    offHeatrun()
                    heat_queue.put(heat_on_image)
                    heat_power_down()
                    if mqtttherm is not None:
                        mqtttherm.publish("Heat","heatoff") # If program closes, esp32 outputs shut off
                    time.sleep(1)
                    mqttOff()
            if heating == "Off":
                if heat_status == "On":
                    offHeatrun()
                    heat_power_down()
                    if mqtttherm is not None:
                        mqtttherm.publish("Heat","heatoff") # If program closes, esp32 outputs shut off
                    mqttOff()
                    break
                else:
                    break
        except:
            if logging_enabled:
                logging.warning('heatmode')
            time.sleep(1)
#            print(exception)

def check_cool_queue():
    try:
        while True:
            cool_image = cool_queue.get_nowait()
            cool_btn.config(image=cool_image)
    except queue.Empty:
        pass

    root.after(200, check_cool_queue)
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
            if sensor_fault:
                if cool_status == "On":
                    offCoolrun()
                    cool_queue.put(cool_on_image)
                    cool_power_down()
                time.sleep(1)
                continue
            if cooling == "On":
                if temp_inside > (setPoint + swing) and cool_status == "Off" and idle_timer == 0 and ac_timeout == "Off":
                    cool()
                    onCoolrun()
                    cool_queue.put(cool_run_image)
                if (temp_inside < (setPoint - swing) and cool_status == "On") or ac_timeout == "On":
                    offCoolrun()
                    cool_queue.put(cool_on_image)
                    cool_power_down()
            if cooling == "Off":
                if cool_status == "On":
                    offCoolrun()
                    cool_power_down()
                    break
                else:
                    break
        except:
            if logging_enabled:
                logging.warning('coolmode')
            time.sleep(1)
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
        if logging_enabled:
            logging.warning('fan_selected')

#		~~Heat Button~~
heat_image = PhotoImage(file=heat_image_path)
heat_on_image = PhotoImage(file=heat_on_image_path)
heat_run_image = PhotoImage(file=heat_run_image_path)
heat_btn = Button(button_frame, image=heat_image, bg="black", borderwidth="0", highlightbackground="black", command=heat_on)
heat_btn.grid(row=2,column=0,padx=padding)

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
cool_btn = Button(button_frame, image=cool_image, bg="black", borderwidth="0", highlightbackground="black", command=cool_on)
cool_btn.grid(row=2,column=2,padx=padding)

#		~~Fan Button~~
fan_image = PhotoImage(file=fan_image_path)
fan_on_image = PhotoImage(file=fan_on_image_path)
fan_btn = Button(button_frame, image=fan_image, bg="black", borderwidth="0", highlightbackground="black", command=fan_on)
fan_btn.grid(row=2,column=4,padx=padding)

#		~~Set Threads to start after window~~
root.after(1000, sensor_thread)
root.after(2000, setpoint_thread)
root.after(3000, time_thread)
root.after(4000, weather_thread)
root.after(200, check_weather_queue)
root.after(200, check_sensor_queue)
root.after(200, check_setpoint_queue)
root.after(200, check_heat_queue)
root.after(200, check_cool_queue)
heat_check()
cool_check()
fan_check()
root.mainloop()
GPIO.cleanup()
