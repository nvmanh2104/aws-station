from ast import literal_eval
from collections import OrderedDict, Mapping
import datetime
import json
import math
import logging
import os
import six
import socket
import ssl
import sys
import threading
import time
import traceback
from utils import events, aws_utils
try:
    import configparser
except:
    from six.moves import configparser

# Import trickery
global HAVE_CV2
global HAVE_MQTT
global HAVE_PIL
HAVE_CV2 = False
HAVE_MQTT = False
HAVE_PIL = False
try:
    import paho.mqtt.client as mqtt
    HAVE_MQTT = True
except ImportError:
    print("paho mqtt client not found")

class AwsMqttClient (object):

    VERSION = "1.0"

    def __init__(self, address="101.96.116.76", port=14688, blid=None, password=None, sendtopic="aws/data",gettopic="aws/control",
                 continuous=True, clean=False, cert_name="", EmqttAWSName="aws",logfile="./aws.log",
                 file="./config.ini"):
        self.address = address
        self.pretty_print = False
        self.stop_connection = False
        self.periodic_connection_running = False
        self.clean = clean
        self.EmqttAWS_port = port #14688#1883#60036 #1883
        self.blid = blid
        self.password = password
        self.EmqttAWSName = EmqttAWSName
        self.gettopic = gettopic
        self.sendtopic = sendtopic
        self.mqttc = None
        self.exclude = ""
        self.delay = 1
        self.EmqttAWS_connected = False
        self.indent = 0
        self.master_indent = 0
        self.raw = False
        self.drawmap = False
        self.previous_co_ords = None #= self.co_ords = self.zero_coords()
        self.fnt = None
        self.home_pos = None
        self.angle = 0
        self.cleanMissionStatus_phase = ""
        self.previous_cleanMissionStatus_phase = ""
        self.current_state = None
        self.last_completed_time = None
        self.bin_full = False
        self.base = None  # base map
        self.dock_icon = None  # dock icon
        self.EmqttAWS_icon = None  # EmqttAWS icon
        self.EmqttAWS_cancelled_icon = None  # EmqttAWS cancelled icon
        self.EmqttAWS_battery_icon = None  # EmqttAWS battery low icon
        self.EmqttAWS_error_icon = None  # EmqttAWS error icon
        self.bin_full_icon = None  # bin full icon
        self.room_outline_contour = None
        self.room_outline = None
        self.transparent = (0, 0, 0, 0)  # transparent
        self.previous_display_text = self.display_text = None
        self.master_state = {}
        self.time = time.time()
        self.update_seconds = 300  # update with all values every 5 minutes
        self.show_final_map = True
        self.client = None
        # Raise event when receive data
        self.message_event = events.EventHandler("message")
        self.log_event = events.EventHandler("log")
        self.error_event = events.EventHandler("error")

    def setup_client(self):
        if self.client is None:
            if not HAVE_MQTT:
                print("Please install paho-mqtt 'pip install paho-mqtt' "
                      "to use this library")
                return False
            self.client = mqtt.Client(client_id=self.EmqttAWSName, clean_session=False, protocol=4)
            # Assign event callbacks
            self.client.on_message = self.on_message
            self.client.on_connect = self.on_connect
            self.client.on_publish = self.on_publish
            self.client.on_subscribe = self.on_subscribe
            self.client.on_disconnect = self.on_disconnect
            self.client.username_pw_set(self.blid, self.password)
            self.client.max_inflight_messages_set(sys.maxsize-1)
            
            return True
        return False

    def connect(self):
        self.setup_client()
        print ("address: %s, port: %d"%(self.address, self.EmqttAWS_port))            
        try:
            print ('-wait until connect success fully')
            self.client.connect(self.address, self.EmqttAWS_port, 60)
            print ('connected!') 
        except Exception as e:
            print(e)
            time.sleep(10)
            self.connect()
           
    def disconnect(self):
        if self.continuous:
            self.client.disconnect()
        else:
            self.stop_connection = True

    def on_connect(self, client, userdata, flags, rc):
        print("EmqttAWS Connected %s" % self.EmqttAWSName)
        if rc == 0:
            self.EmqttAWS_connected = True
            self.client.subscribe(self.gettopic, 1)
        else:
            print ("EmqttAWS Connected with result code " + str(rc))
            print ("Please make sure your blid and password are "
                           "correct %s" % self.EmqttAWSName)
            if self.mqttc is not None:
               self.mqttc.disconnect()
            sys.exit(1)

    def on_message(self, mosq, obj, msg):
        print( "topic:%s, qos:%s, dup:%s, retain:%s, message:%s"%(msg.topic, str(msg.qos), str(msg.dup), str(msg.retain), msg.payload))
        # Raise Event message
        self.message_event(msg) 
            #Raise Loge message          
            #message = aws_utils.decode_payload(msg.payload)
            #if message.__contains__("RT"):
            #    dateTimeData = aws_utils.get_respone_time_server(message["sID"])                
            #    self.client.publish(self.sendtopic,dateTimeData)
            #else:
                # Raise Event message
            #    self.message_event(msg)  
    def on_publish(self, mosq, obj, mid):
        pass

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        print("Subscribed: %s %s" % (str(mid), str(granted_qos)))

    def on_disconnect(self, mosq, obj, rc):
        self.EmqttAWS_connected = False
        if rc != 0:            
            print ("Unexpected Disconnect From EmqttAWS %s! - reconnecting" % self.EmqttAWSName)
        else:
            print ("Disconnected From EmqttAWS %s" % self.EmqttAWSName)

    def on_log(self, mosq, obj, level, string):
        print(string)

    def publish(self, topic, message):
        if self.client is not None and message is not None:
            print("Publishing item: %s: %s"
                           % (topic, message))
            #print message          
            self.client.publish(topic, message, qos=1, retain=False)
    
    def run(self):
        self.client.loop_forever()
    
if __name__ == '__main__':
    aws_client = EmqttAWS()
    aws_client.connect();
