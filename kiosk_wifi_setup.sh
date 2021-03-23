#!/bin/bash
x=`ifconfig wlan0 | grep "inet "`
while [ "$x" = "" ]
do
    echo Connecting
    matchbox-keyboard
    # onboard -D 0.0 -x 20 -y 400
    x=`ifconfig wlan0 | grep "inet "`
done

chromium-browser --kiosk http://127.0.0.1
