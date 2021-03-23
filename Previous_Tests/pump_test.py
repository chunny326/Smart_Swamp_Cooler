#!/usr/bin/python3.7

from gpiozero import LED
from time import sleep

speed = LED(21)
fan   = LED(20)
pump  = LED(16)
delay = 2

done = False
while not done:
    print('Pump Test starting...')
    sleep(1.5*delay)
    print('Turn on pump')
    pump.on()
    sleep(10*delay)
    print('Pump off')
    pump.off()
    done=True


