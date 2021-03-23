#!/usr/bin/python3.7

from gpiozero import LED
from time import sleep

speed = LED(21)
fan   = LED(20)
pump  = LED(16)
delay = 5

done = False
while not done:
    print('Stress test starting...')
    sleep(2)
    print('Turn on pump')
    pump.on()
    sleep(delay)
    print('Low speed fan')
    fan.on()
    sleep(delay)
    print('Hi speed fan')
    speed.on()
    sleep(delay)
    print('Fan off')
    speed.off()
    fan.off()
    sleep(delay)

    print('Pump off')
    pump.off()
    done=True


