"""
David Carlson & Bryce Martin
ECE 4800 Senior Design Project

This file is used solely for DEBUG and running the 
RPi Sprinkler Controller code on a windows computer
    This was done to facilitate AndroidApp development
    where access to the full RPi+XbeeCoordinator+Nodes
    and actual sensors was unavailable/inconvenient.

"""
import argparse
import sys
import os
import threading
import json
from sys import platform


SensorStats = [
    {'Tilt': 1, 'Sector': 0, 'Moisture': 3333, 'Sunlight': 3666, 'Battery': 2284, 'Timestamp': 1572840686, 'Minute': 11, 'Hour': 21, 'Day': 17, 'Month': 11, 'Year': 2019, 'Temperature': 25.2, 'Humidity': 30.5, 'Wind': 2.748697642481118},
    {'Tilt': 1, 'Sector': 1, 'Moisture': 3456, 'Sunlight': 3887, 'Battery': 2289, 'Timestamp': 1572840686, 'Minute': 11, 'Hour': 21, 'Day': 17, 'Month': 11, 'Year': 2019, 'Temperature': 27.2, 'Humidity': 41.5, 'Wind': 2.748697642481118},
    {'Tilt': 1, 'Sector': 2, 'Moisture': 2011, 'Sunlight': 3667, 'Battery': 2288, 'Timestamp': 1572840686, 'Minute': 11, 'Hour': 21, 'Day': 17, 'Month': 11, 'Year': 2019, 'Temperature': 26.5, 'Humidity': 41.5, 'Wind': 2.748697642481118},
    {'Tilt': 0, 'Sector': 3, 'Moisture': 2001, 'Sunlight': 3988, 'Battery': 2285, 'Timestamp': 1572840686, 'Minute': 11, 'Hour': 21, 'Day': 17, 'Month': 11, 'Year': 2019, 'Temperature': 27.4, 'Humidity': 45.5, 'Wind': 2.748697642481118}
]



class fakeIO():
        temperature = 0
        humidity = 0
        voltage = 0
        def __init__(self, val1, val2):
            self.val1 = val1
            self.val2 = val2
            # self.val3 = val3
        def SPI(clock, MISO, MOSI):
            clock = clock
            MISO = MISO
            MOSI = MOSI
            return 0
        def DigitalInOut(self):
            self.board = self
            return 0
        def SCK(self):
            return 0
        def MISO(self):
            return 0
        def MOSI(self):
            return 0
        def Serial(val1, val2):
            val1 = val1
            val2 = val2
            inWaiting = 0
            return fakeIO
            def inWaiting():
                return 0
            def SerialException():
                return 0
        def MCP3008(val1, val2):
            val1 = val1
            val2 = val2
            return 0
        def DHT22(self):
            temperature = 0
            humidity = 0
            return fakeIO
        def D25(self):
            self.board = self
            return 0
        def D21(self):
            self.board = self
            return 0
        def P0(self):
            self.board = self
        def inWaiting():
            return 0
        def close():
            return 0
        def AnalogIn(self, val1, val2):
            voltage = 0

class fakeIO2():
        def __init__(self, pin):
            self.pin = pin
            self.enabled = False
            self.direction = False
        def direction(self, dir):
            self.direction = dir
        def value(self, en):
            self.enable = en

