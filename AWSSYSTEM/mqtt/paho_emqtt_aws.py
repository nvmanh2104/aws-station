from ast import literal_eval
from collections import OrderedDict, Mapping
try:
    from roomba.password import Password
except ImportError:
    from password import Password

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
try:
    import cv2
    import numpy as np
    HAVE_CV2 = True
except ImportError:
    print("CV or numpy module not found, falling back to PIL")

# NOTE: MUST use Pillow Pillow 4.1.1 to avoid some horrible memory leaks in the
# text handling!
try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
    HAVE_PIL = True
except ImportError:
    print("PIL module not found, maps are disabled")

# On Python 3 raw_input was renamed to input
try:
    input = raw_input
except NameError:
    pass

'''
def on_connect(client, userdata, flags, rc):
    print ('Connected with result code: ' + str(rc))
    client.subscribe("test/demo")

def on_message (client, userdata, msg):
    if msg is not None:
        if (msg.topic is not None) and (msg.payload is not None):
            # print ("new data from " + msg.topic)
            text_file = open("F:\Output.txt", "w")
            text_file.write(msg.payload)
            text_file.close()
# Ten file: VinaRain_yyyyMMddHHmmss.txt
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect("192.168.1.67",1883,60)
client.loop_forever()
'''

class EmqttAWS (object):

    VERSION = "1.0"

    states = {"charge": "Charging",
              "new": "New Mission",
              "run": "Running",
              "resume": "Running",
              "hmMidMsn": "Recharging",
              "recharge": "Recharging",
              "stuck": "Stuck",
              "hmUsrDock": "User Docking",
              "dock": "Docking",
              "dockend": "Docking - End Mission",
              "cancelled": "Cancelled",
              "stop": "Stopped",
              "pause": "Paused",
              "hmPostMsn": "End Mission",
              "": None}

    # From http://homesupport.irobot.com/app/answers/detail/a_id/9024/~/EmqttAWS-900-error-messages
    _ErrorMessages = {
        0: "None",
        1: "EmqttAWS is stuck with its left or right wheel hanging down.",
        2: "The debris extractors can't turn.",
        5: "The left or right wheel is stuck.",
        6: "The cliff sensors are dirty, it is hanging over a drop, " \
           "or it is stuck on a dark surface.",
        8: "The fan is stuck or its filter is clogged.",
        9: "The bumper is stuck, or the bumper sensor is dirty.",
        10: "The left or right wheel is not moving.",
        11: "EmqttAWS has an internal error.",
        14: "The bin has a bad connection to the robot.",
        15: "EmqttAWS has an internal error.",
        16: "EmqttAWS has started while moving or at an angle, or was bumped " \
            "while running.",
        17: "The cleaning job is incomplete.",
        18: "EmqttAWS cannot return to the Home Base or starting position."
    }

    def __init__(self, address="101.96.116.76", port=14688, blid=None, password=None, sendtopic="aws/data",gettopic="aws/control",
                 continuous=True, clean=False, cert_name="", EmqttAWSName="aws",logfile="./aws.log",
                 file="./config.ini"):
        self.debug = False
        self.log = logging.getLogger(__name__+'.EmqttAWS')
        self.hdlr = logging.FileHandler(logfile)
        #formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        #hdlr.setFormatter(formatter)
        self.log.addHandler(self.hdlr)


        if self.log.getEffectiveLevel() == logging.DEBUG:
            self.debug = True
        self.address = address
        '''
        if not cert_name:
            self.cert_name = "/etc/ssl/certs/ca-certificates.crt"
        else:
            self.cert_name = cert_name
        '''
        self.continuous = continuous
        if self.continuous:
            self.log.info("CONTINUOUS connection")
        else:
            self.log.info("PERIODIC connection")
        # set the following to True to enable pretty printing of json data
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
            self.client = mqtt.Client(client_id=self.EmqttAWSName, clean_session=False, protocol=3)
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
        if self.address is None:
            self.log.critical("Invalid address!")
            sys.exit(1)
        if self.EmqttAWS_connected or self.periodic_connection_running: return

        if self.continuous:
            if not self._connect():
                if self.mqttc is not None:
                    self.mqttc.disconnect()
                sys.exit(1)
        else:
            self._thread = threading.Thread(target=self.periodic_connection)
            self._thread.daemon = True
            self._thread.start()

        self.time = time.time()   #save connect time

    def _connect(self, count=0, new_connection=False):
        max_retries = 3
        try:
            if self.client is None or new_connection:
                self.log.info("Connecting %s" % self.EmqttAWSName)
                self.setup_client()
                self.client.connect(self.address, self.EmqttAWS_port, 60)
            else:
                self.log.info("Attempting to Reconnect %s" % self.EmqttAWSName)
                self.client.loop_stop()
                self.client.reconnect()
            self.client.loop_start()
            return True
        except Exception as e:
            self.log.error("Error: %s " % e)
            exc_type, exc_obj, exc_tb = sys.exc_info()
            # self.log.error("Exception: %s" % exc_type)
            # if e[0] == 111: #errno.ECONNREFUSED - does not work with
            # python 3.0 so...
            if exc_type == socket.error or exc_type == 111:
                count += 1
                if count <= max_retries:
                    self.log.error("Attempting new Connection# %d" % count)
                    time.sleep(1)
                    self._connect(count, True)
        if count == max_retries:
            self.log.error("Unable to connect %s" % self.EmqttAWSName)
        return False

    def disconnect(self):
        if self.continuous:
            self.client.disconnect()
        else:
            self.stop_connection = True

    def periodic_connection(self):
        # only one connection thread at a time!
        if self.periodic_connection_running: return
        self.periodic_connection_running = True
        while not self.stop_connection:
            if self._connect():
                time.sleep(self.delay)
                self.client.disconnect()
            time.sleep(self.delay)

        self.client.disconnect()
        self.periodic_connection_running = False

    def on_connect(self, client, userdata, flags, rc):
        self.log.info("EmqttAWS Connected %s" % self.EmqttAWSName)
        print("EmqttAWS Connected %s" % self.EmqttAWSName)
        if rc == 0:
            self.EmqttAWS_connected = True
            self.client.subscribe(self.gettopic, 1)
        else:
            self.log.error("EmqttAWS Connected with result code " + str(rc))
            print ("EmqttAWS Connected with result code " + str(rc))
            self.log.error("Please make sure your blid and password are "
                           "correct %s" % self.EmqttAWSName)
            print ("Please make sure your blid and password are "
                           "correct %s" % self.EmqttAWSName)
            if self.mqttc is not None:
               self.mqttc.disconnect()
            sys.exit(1)

    def on_message(self, mosq, obj, msg):
        print( "topic:%s, qos:%s, dup:%s, retain:%s, message:%s"%(msg.topic, str(msg.qos), str(msg.dup), str(msg.retain), msg.payload))
        if self.exclude != "":
            if self.exclude in msg.topic:
                return

        if self.indent == 0:
            self.master_indent = max(self.master_indent, len(msg.topic))

        #log_string, json_data = self.decode_payload(msg.topic,msg.payload)
        #self.dict_merge(self.master_state, json_data)
        log_string = "test"
        if self.pretty_print:
            self.log.info("%-{:d}s : %s".format(self.master_indent)
                          % (msg.topic,log_string))
        else:
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
        '''
        if self.raw:
            self.publish(msg.topic, msg.payload)
        else:
            self.decode_topics(json_data)
        '''
        # default every 5 minutes
        if time.time() - self.time > self.update_seconds:
            self.log.info("Publishing master_state %s" % self.EmqttAWSName)
            self.decode_topics(self.master_state)    # publish all values
            self.time = time.time()

    def on_publish(self, mosq, obj, mid):
        pass

    def on_subscribe(self, mosq, obj, mid, granted_qos):
        self.log.debug("Subscribed: %s %s" % (str(mid), str(granted_qos)))

    def on_disconnect(self, mosq, obj, rc):
        self.EmqttAWS_connected = False
        if rc != 0:
            self.log.warn("Unexpected Disconnect From EmqttAWS %s! - reconnecting"
                          % self.EmqttAWSName)
            print ("Unexpected Disconnect From EmqttAWS %s! - reconnecting" % self.EmqttAWSName)
        else:
            self.log.info("Disconnected From EmqttAWS %s" % self.EmqttAWSName)
            print ("Disconnected From EmqttAWS %s" % self.EmqttAWSName)

    def on_log(self, mosq, obj, level, string):
        self.log.info(string)

    def set_mqtt_client(self, mqttc=None, brokerFeedback=""):
        self.mqttc = mqttc
        if self.mqttc is not None:
            if self.EmqttAWSName != "":
                self.brokerFeedback = brokerFeedback + "/" + self.EmqttAWSName
            else:
                self.brokerFeedback = brokerFeedback

    def send_command(self, command):
        self.log.info("Received COMMAND: %s" % command)
        Command = OrderedDict()
        Command["command"] = command
        Command["time"] = self.totimestamp(datetime.datetime.now())
        Command["initiator"] = "localApp"
        myCommand = json.dumps(Command)
        self.log.info("Publishing EmqttAWS Command : %s" % myCommand)
        self.client.publish("cmd", myCommand)

    def set_preference(self, preference, setting):
        self.log.info("Received SETTING: %s, %s" % (preference, setting))
        val = False
        if setting.lower() == "true":
            val = True
        tmp = {preference: val}
        Command = {"state": tmp}
        myCommand = json.dumps(Command)
        self.log.info("Publishing EmqttAWS Setting : %s" % myCommand)
        self.client.publish("delta", myCommand)

    def publish(self, topic, message):
        if self.client is not None and message is not None:
            self.log.debug("Publishing item: %s: %s"
                           % (topic, message))
            print("Publishing item: %s: %s"
                           % (topic, message))
            #print message
            #self.mqttc.publish(self.brokerFeedback + "/" + topic, message)
            self.client.publish(topic, message, qos=1, retain=False)

    def set_options(self, raw=False, indent=0, pretty_print=False):
        self.raw = raw
        self.indent = indent
        self.pretty_print = pretty_print
        if self.raw:
            self.log.info("Posting RAW data")
        else:
            self.log.info("Posting DECODED data")
    def decode_payload(self, topic, payload):
        '''
        Format json for pretty printing, return string sutiable for logging,
        and a dict of the json data
        '''
        indent = self.master_indent + 31 #number of spaces to indent json data

        try:
            # if it's json data, decode it (use OrderedDict to preserve keys
            # order), else return as is...
            json_data = json.loads(
                payload.decode("utf-8").replace(":nan", ":NaN").\
                replace(":inf", ":Infinity").replace(":-inf", ":-Infinity"),
                object_pairs_hook=OrderedDict)
            # if it's not a dictionary, probably just a number
            if not isinstance(json_data, dict):
                return json_data, dict(json_data)
            json_data_string = "\n".join((indent * " ") + i for i in \
                (json.dumps(json_data, indent = 2)).splitlines())

            formatted_data = "Decoded JSON: \n%s" % (json_data_string)

        except ValueError:
            formatted_data = payload

        if self.raw:
            formatted_data = payload

        return formatted_data, dict(json_data)

    def decode_topics(self, state, prefix=None):
        '''
        decode json data dict, and publish as individual topics to
        brokerFeedback/topic the keys are concatinated with _ to make one unique
        topic name strings are expressely converted to strings to avoid unicode
        representations
        '''
        for k, v in six.iteritems(state):
            if isinstance(v, dict):
                if prefix is None:
                    self.decode_topics(v, k)
                else:
                    self.decode_topics(v, prefix+"_"+k)
            else:
                if isinstance(v, list):
                    newlist = []
                    for i in v:
                        if isinstance(i, dict):
                            for ki, vi in six.iteritems(i):
                                newlist.append((str(ki), vi))
                        else:
                            if isinstance(i, six.string_types):
                                i = str(i)
                            newlist.append(i)
                    v = newlist
                if prefix is not None:
                    k = prefix+"_"+k
                # all data starts with this, so it's redundant
                k = k.replace("state_reported_","")
                # save variables for drawing map
                if k == "pose_theta":
                    self.co_ords["theta"] = v
                if k == "pose_point_x": #x and y are reversed...
                    self.co_ords["y"] = v
                if k == "pose_point_y":
                    self.co_ords["x"] = v
                if k == "bin_full":
                    self.bin_full = v
                if k == "cleanMissionStatus_error":
                    try:
                        self.error_message = self._ErrorMessages[v]
                    except KeyError as e:
                        self.log.warn(
                            "Error looking up EmqttAWS error message %s" % e)
                        self.error_message = "Unknown Error number: %d" % v
                    self.publish("error_message", self.error_message)
                if k == "cleanMissionStatus_phase":
                    self.previous_cleanMissionStatus_phase = \
                        self.cleanMissionStatus_phase
                    self.cleanMissionStatus_phase = v

                self.publish(k, str(v))

        if prefix is None:
            self.update_state_machine()

    def update_state_machine(self, new_state = None):
        '''
        EmqttAWS progresses through states (phases), current identified states
        are:
        ""              : program started up, no state yet
        "run"           : running on a Cleaning Mission
        "hmUsrDock"     : returning to Dock
        "hmMidMsn"      : need to recharge
        "hmPostMsn"     : mission completed
        "charge"        : chargeing
        "stuck"         : EmqttAWS is stuck
        "stop"          : Stopped
        "pause"         : paused

        available states:
        states = {  "charge":"Charging",
                    "new":"New Mission",
                    "run":"Running",
                    "resume":"Running",
                    "hmMidMsn":"Recharging",
                    "recharge":"Recharging",
                    "stuck":"Stuck",
                    "hmUsrDock":"User Docking",
                    "dock":"Docking",
                    "dockend":"Docking - End Mission",
                    "cancelled":"Cancelled",
                    "stop":"Stopped",
                    "pause":"Paused",
                    "hmPostMsn":"End Mission",
                    "":None}

        Normal Sequence is "" -> charge -> run -> hmPostMsn -> charge
        Mid mission recharge is "" -> charge -> run -> hmMidMsn -> charge
                                   -> run -> hmPostMsn -> charge
        Stuck is "" -> charge -> run -> hmPostMsn -> stuck
                    -> run/charge/stop/hmUsrDock -> charge
        Start program during run is "" -> run -> hmPostMsn -> charge

        Need to identify a new mission to initialize map, and end of mission to
        finalise map.
        Assume  charge -> run = start of mission (init map)
                stuck - > charge = init map
        Assume hmPostMsn -> charge = end of mission (finalize map)
        Anything else = continue with existing map
        '''

        current_mission = self.current_state

        #if self.current_state == None: #set initial state here for debugging
        #    self.current_state = self.states["recharge"]
        #    self.show_final_map = False

        #  deal with "bin full" timeout on mission
        try:
            if (self.master_state["state"]["reported"]["cleanMissionStatus"]["mssnM"] == "none" and
                self.cleanMissionStatus_phase == "charge" and
                (self.current_state == self.states["pause"] or
                 self.current_state == self.states["recharge"])):
                self.current_state = self.states["cancelled"]
        except KeyError:
            pass

        if (self.current_state == self.states["charge"] and
                self.cleanMissionStatus_phase == "run"):
            self.current_state = self.states["new"]
        elif (self.current_state == self.states["run"] and
                self.cleanMissionStatus_phase == "hmMidMsn"):
            self.current_state = self.states["dock"]
        elif (self.current_state == self.states["dock"] and
                self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["recharge"]
        elif (self.current_state == self.states["recharge"] and
                self.cleanMissionStatus_phase == "charge" and self.bin_full):
            self.current_state = self.states["pause"]
        elif (self.current_state == self.states["run"] and
                self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["recharge"]
        elif (self.current_state == self.states["recharge"]
                and self.cleanMissionStatus_phase == "run"):
            self.current_state = self.states["pause"]
        elif (self.current_state == self.states["pause"]
                and self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["pause"]
            # so that we will draw map and can update recharge time
            current_mission = None
        elif (self.current_state == self.states["charge"] and
                self.cleanMissionStatus_phase == "charge"):
            # so that we will draw map and can update charge status
            current_mission = None
        elif ((self.current_state == self.states["stop"] or
                self.current_state == self.states["pause"]) and
                self.cleanMissionStatus_phase == "hmUsrDock"):
            self.current_state = self.states["cancelled"]
        elif ((self.current_state == self.states["hmUsrDock"] or
                self.current_state == self.states["cancelled"]) and
                self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["dockend"]
        elif (self.current_state == self.states["hmPostMsn"] and
                self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["dockend"]
        elif (self.current_state == self.states["dockend"] and
                self.cleanMissionStatus_phase == "charge"):
            self.current_state = self.states["charge"]

        else:
            self.current_state = self.states[self.cleanMissionStatus_phase]

        if new_state is not None:
            self.current_state = self.states[new_state]
            self.log.info("set current state to: %s" % (self.current_state))

        if self.current_state != current_mission:
            self.log.info("updated state to: %s" % (self.current_state))

        self.publish("state", self.current_state)
        #self.draw_map(current_mission != self.current_state)


if __name__ == '__main__':
    aws_client = EmqttAWS()
    aws_client.connect();