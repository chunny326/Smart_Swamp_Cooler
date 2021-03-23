#!/usr/bin/python3.7

from gpiozero import LED
from time import sleep

speed = LED(21)
fan   = LED(20)
pump  = LED(16)
delay = 20

done = False
while not done:
    print('Low fan test starting...')
    sleep(delay/10)
    print('Turn on fan')
    fan.on()
    sleep(delay)
    print('Hi fan test ...')
    speed.on()
    sleep(delay)
    print('Low fan test ...')
    speed.off()
    sleep(delay)
    print('fans off')
    fan.off()
    done=True


