#!/usr/bin/python
import datetime
import threading
import os
import time
import RPi.GPIO as GPIO
from weather import *  # import weather because we cant import database


path = os.path.expanduser

#		~~GPIO Setup~~
GPIO.setmode(GPIO.BOARD)# The GPIO board mode setting
GPIO.setwarnings(False)
fan_pin = 36		# ~~Pin for activating the fan.~~
GPIO.setup(fan_pin, GPIO.OUT)
GPIO.output(fan_pin, GPIO.LOW)
ac_pin = 38		# ~~Pin for air conditioning.~~
GPIO.setup(ac_pin, GPIO.OUT)
GPIO.output(ac_pin, GPIO.LOW)
heater_pin = 40		# ~~Pin for Heat~~
GPIO.setup(heater_pin, GPIO.OUT)
GPIO.output(heater_pin, GPIO.LOW)
esp32feedback_pin = 32 # ~~Feedback to esp32 trigger to short pins 5 & 6~~
GPIO.setup(esp32feedback_pin, GPIO.OUT)
GPIO.output(esp32feedback_pin, GPIO.HIGH)

#		~~Variables~~
idle_timer = 0
heat_status = "Off"
cool_status = "Off"
ac_timeout = "Off"
heat_timeout = "Off"

#		~~Control~~
def cool():
    try:
        global heat_status, cool_status
        GPIO.output(ac_pin, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(fan_pin, GPIO.HIGH)
        GPIO.output(heater_pin, GPIO.LOW)
        heat_status = "Off"
        cool_status = "On"
        timeoutcool_thread()
        return heat_status, cool_status
    except:
        return

def heartbeat_thread():
    command=threading.Thread(target=heart_get, daemon=True).start()
    return
def heart_get():
    seconds = 60
    while True:
        setPoint = getSetpoint()
        test = setPoint
        try:
            if setPoint == test:
                try:
                    for x in range(seconds):
                        seconds = seconds - 1
                        time.sleep(1)
                        setPoint = getSetpoint()
                    print('reboot')
                    return
                except:
                    return
            else:
                print('recount')
                return

        except:
            print('heartexcept')

def timeoutcool_thread():
    command=threading.Thread(target=timeoutcool, daemon=True).start()
    return
def timeoutcool():
    global ac_timeout
    seconds = 5400 #1200 seconds = 20 minutes, 1800 = 30, 3600 = 60
    while True:
        try:
            for x in range(seconds):
                seconds = seconds - 1
                time.sleep(1)
                if cool_status == "Off":
                    break
            ac_timeout = "On"
            hvackill()
            break
        except:
            print('timeoutcoolexception')

def heat():
    try:
        global heat_status, cool_status
        GPIO.output(heater_pin, GPIO.HIGH)
        heat_status = "On"
        GPIO.output(ac_pin, GPIO.LOW)
        cool_status = "Off"
        timeoutheat_thread()
        return heat_status, cool_status
    except:
        return

def timeoutheat_thread():
    command=threading.Thread(target=timeoutheat, daemon=True).start()
    return
def timeoutheat():
    global heat_timeout
    seconds = 1800 #1200 seconds = 20 minutes, 1800 = 30, 3600 = 60
    while True:
        try:
            for x in range(seconds):
                seconds = seconds - 1
                time.sleep(1)
                if heat_status == "Off":
                    break
            heat_timeout = "On"
            print('timeout')
            hvackill()
            break
        except:
            print('timeoutheatexception')

#		~~Runs heat_power_down and cool_power_down if main program doesnt respond~~
def hvackill():
    try:
        time.sleep(15)
        if heat_timeout == "On" and heat_status == "On":
            print('hvacheatkill')
            heat_power_down()
            return
        if cool_timeout == "On" and cool_status == "On":
            cool_power_down()
            return
        else:
            return
        return
    except:
        return

def fan_only():
    try:
        global heat_status, cool_status
#   ~~To blow the rest of the cooled air out of the system~~
        GPIO.output(heater_pin, GPIO.LOW)
        heat_status = "Off"
        GPIO.output(ac_pin, GPIO.LOW)
        cool_status = "Off"
        GPIO.output(fan_pin, GPIO.HIGH)
        return heat_status, cool_status
    except:
        return

def idle():
    try:
        global idle_timer, ac_timeout, heat_timeout
        fan_value = getFandata()  #   ~~import from weather, wont allow import from database.  Called too many times...~~
        if fan_value != 1:
            GPIO.output(fan_pin, GPIO.LOW)
#          delay to preserve compressor
        idle_timer = 1
        time.sleep(420) #420
        ac_timeout = "Off"
        heat_timeout = "Off"
        idle_timer = 0
        return idle_timer, ac_timeout, heat_timeout
    except:
        print('idleexception')
#        print(idleexception)
        return

#		~~Shutoff A/C after Setpoint is reached~~
#		~~And run fan for 60 second after~~
def cool_power_down():
    try:
        global cool_status
        GPIO.output(ac_pin, GPIO.LOW)
        cool_status = "Off"
        fan_only()
        time.sleep(120)
        return cool_status, idle()
    except:
        return

#		~~Shutoff Heat after Setpoint is reached~~
def heat_power_down():
    try:
        global heat_status
        GPIO.output(heater_pin, GPIO.LOW)
        print(heat_status)
        heat_status = "Off"
        fan_only()
        time.sleep(120)
        return heat_status, idle()
    except:
        print('heatpowerdownexception')

#               ~~Variables~~
def getvariables():
    try:
        return heat_status, cool_status, idle_timer, heat_timeout, ac_timeout
    except:
        return

def fanSet():
    try:
        GPIO.output(fan_pin, GPIO.HIGH)
        return
    except:
        return

def fanOff():
    try:
        GPIO.output(fan_pin, GPIO.LOW)
        return
    except:
        return
