import paho.mqtt.client as mqtt
from time import sleep


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("test/demo")
    #client.publish("test/demo", "Anh Huy dem trai .........")
    isrunning = True


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    pass


def on_sendmessage():
    #client.publish("test/demo", "Anh Huy dem trai .........")
    flex = open("/home/cntt/aws/files/test.json", "r")
    message = flex.read();
    flex.close()
    client.publish("test/demo", message)
    print ("send data sucessfully!")

isrunning = False
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.67", 1883, 60)  # window:192.168.1.70, linux:192.168.1.150

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()
client.loop_start()
print ("Testing is running...!")
while True:
    on_sendmessage()
    sleep(600)

