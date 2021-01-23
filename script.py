#try:
#    port = serial.Serial("/dev/serial1", baudrate=9600, timeout=3.0)
#except serial.SerialException:
#    print("Serial conncetion failed.")

#print("Start")
#while True:
    #if port.inWaiting() > 0:
    #    rcv = str(port.readline(), "utf-8")
#    rcv = port.read(10)
    
#    print(repr(rcv))
#    print("\n")

import time
import serial
import RPi.GPIO as GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup Serial
ser = serial.Serial(
    port = '/dev/ttyS0',
    baudrate = 57600,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)

while 1:
    x = ser.readline()
    print(x)


