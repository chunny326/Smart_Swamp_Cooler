"""
Bryce Martin and David Carlson

ECE 4800 - Senior Project

Network setup pulled from Digi manual for XBee3 quick setup/start

This code runs on the Xbee3 acting as a coordinator receiving data it
collects from the nodes. This data is then relayed to the main brain board.
"""
import xbee
import time


print("Forming a new Zigbee network as a coordinator...")
xbee.atcmd("NI", "Coordinator Hub")

# NJ should be changed in the final product
network_settings = {"BD": 0x7, "CE": 1, "EE": 0, "ID": 0xABCD, "NJ": 0xFF, "PS": 1}

for command, value in network_settings.items():
    xbee.atcmd(command, value)
xbee.atcmd("AC") # Apply changes
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
    dest_addr = node['sender_nwk']  # using 16 bit addressing
    dest_node_id = node['node_id']
    payload_data = "Hello, " + dest_node_id + "!"
    print("Sending \"{}\" to {}".format(payload_data, hex(dest_addr)))
    xbee.transmit(dest_addr, payload_data)

print("Receiving data...")

temp = {}
while True:
    temp = xbee.receive()
    if temp:
        print(temp)
        # From here the 'payload' key can be used to pull the data sent from the sensors
        temp.clear()
    time.sleep_ms(250) # wait 0.25 seconds before checking again
