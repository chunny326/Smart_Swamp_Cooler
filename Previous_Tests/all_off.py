#!/usr/bin/python3.7

from gpiozero import LED
from time import sleep

speed = LED(16)
fan   = LED(21)
pump  = LED(20)
delay = 2

done = False
while not done:
    print('All Off...')
    speed.off()
    pump.off()
    fan.off()
    done=True


