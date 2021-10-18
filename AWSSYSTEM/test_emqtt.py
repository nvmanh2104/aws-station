import paho.mqtt.client as mqtt
from time import sleep
import datetime

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("aws/getdata")
    #client.publish("test/demo", "Anh Huy dem trai .........")
    isrunning = True


# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    lengthData = len(msg.payload)
    message =  msg.payload
    print (msg.payload)


def on_sendmessage():
    #client.publish("test/demo", "Anh Huy dem trai .........")
    #flex = open("/home/cntt/aws/files/test.json", "r")
    flex = open("C:\\Users\\manhn\\OneDrive\\sourcecode\\vnmha\\pycharm-workspace\\AWSSYSTEM\\ClientSenData.json", "r")
    message = flex.read()
    messageLenth = len(message)

    flex.close()
    client.publish("aws/senddata", message)
    print ("send data sucessfully!")

date_time_str = '2019-8-14T14:50:20'
date_time_obj = datetime.datetime.strptime(date_time_str, '%Y-%m-%dT%H:%M:%S')
print('Date:', date_time_obj.date())
print('Time:', date_time_obj.time())
print('Date-time:', date_time_obj)

isrunning = False
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set("aws","aws123123")

client.connect("aws1.weathervietnam.vn", 1883, 60)  # window:192.168.1.70, linux:192.168.1.150

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()
client.loop_start()
print ("Testing is running...!")
while True:
    on_sendmessage()
    sleep(10)

