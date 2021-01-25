"""
Jayden Smith

Last Modified: January 25, 2021

ECE 4020 - Senior Project II

Network setup for XBee3 quick setup/start

This code runs on the Xbee3 acting as a coordinator receiving data it
collects from the nodes. This data is then relayed to the serial port
of the MC (Raspberry Pi 4).
"""

import xbee
import time

print("Forming a new Zigbee network as a coordinator...")
xbee.atcmd("NI", "Coordinator Hub")
# "BD": 0x3 => 9600, 0x7 => 115200
network_settings = {"CE": 1, "ID": 0xABCD, "BD": 0x6, "NJ": 0xFF}
# "BD": 0x7, "EE": 0, "PS": 1
for command, value in network_settings.items():
    xbee.atcmd(command, value)
xbee.atcmd("AC")  # Apply changes
time.sleep(1)

# Query AI until it reports success
while xbee.atcmd("AI") != 0:
    time.sleep_ms(100)

print("Network Established\n")
print("Waiting for a remote node to join...")

node_list = []
while len(node_list) == 0:  # Perform a network discovery until the router joins
    node_list = list(xbee.discover())
print("Remote node found, transmitting data")

for node in node_list:
    dest_addr = node['sender_nwk']  # using 16-bit addressing
    dest_node_id = node['node_id']
    payload_data = "Hello, " + dest_node_id + "!"
    print("Sending \"{}\" to {}".format(payload_data, hex(dest_addr)))
    # checked for 2-way communication with line below
    # xbee.transmit(dest_addr, payload_data)

print("Receiving data...")

received_msg = {}
while True:
    received_msg = xbee.receive()
    if received_msg:
        # From here the 'payload' key can be used to pull the data sent from the sensors
        print(received_msg)
        received_msg.clear()
    time.sleep_ms(250)  # sleep for 0.25 seconds before checking again
