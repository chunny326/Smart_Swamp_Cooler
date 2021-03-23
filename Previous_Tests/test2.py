#!/usr/bin/python3.7

from gpiozero import LED
from time import sleep

speed = LED(16)
fan   = LED(21)
pump  = LED(20)
delay = 2

done = False
while not done:
    print('Test starting...')
    sleep(1.5*delay)
    print('Turn on pump')
    pump.on()
    sleep(delay)
    print('Turn on lowspeed fan')
    fan.on()
    sleep(delay)
    print('High speed fan')
    speed.on()
    sleep(delay)
    print('Low speed fan')
    speed.off()
    sleep(delay)
    print('Pump off')
    pump.off()
    sleep(delay)
    print('Fan off')
    fan.off()
    sleep(delay)
    done=True


