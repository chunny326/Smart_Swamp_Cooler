#!/bin/bash
sleep 5

x=`ifconfig wlan0 | grep "inet "`
while [ "$x" = "" ]
do
    echo Connecting
    matchbox-keyboard
    x=`ifconfig wlan0 | grep "inet "`
done

chromium-browser --kiosk http://127.0.0.1
