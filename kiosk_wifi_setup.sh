#!/bin/bash
x=`ifconfig wlan0 | grep "inet "`
while [ "$x" = "" ]
do
    echo Connecting
    matchbox-keyboard & wpa_gui
    x=`ifconfig wlan0 | grep "inet "`
done

chromium-browser --kiosk http://127.0.0.1
