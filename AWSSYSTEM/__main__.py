import logging
from mqtt import aws_mqtt_client
from utils import events,aws_utils
from mogodriver import mongodriver
import os
import time
from pymongo import MongoClient,ReadPreference
from time import sleep
import datetime
import pytz
import threading
import json
from paho.mqtt.client import MQTTMessage

import hashlib
try:
    import queue
except ImportError:
    import Queue as queue

STATION_CREATED = 'station_created'
STATION_UPDATED = 'station_updated'

def message_handler(sender, msg):
    # write data into queue 
    message_queue.put_nowait(msg)

def process_station_event(msg):
    station = msg['new_entity']
    station_id = station['StationID']
    tail = 0
    for character in station_id:
        tail += ord(character)
    tail = tail * 3 + 1
    pass_word = '%s@%d' % (station_id, tail)

    m = hashlib.sha256()
    encoded_string = pass_word.encode()
    byte_array = bytearray(encoded_string)
    m.update(byte_array)
    
    pass_word = m.hexdigest()
    # update database
    data = {'username': station_id, 'password': pass_word, 'is_superuser': False, 'salt': ''}
    datadriver.insert_user_password(data)

def insert_database():
    while True:
        msg = message_queue.get()            

        dup = msg.dup        
        if dup:
           continue
        
        message = aws_utils.decode_payload(msg.payload)        
        if message is None:
            continue 
        try:           
            if message.__contains__("event_type"):
                if message['event_type'] == STATION_CREATED:
                    process_station_event(message)

        except Exception as e:           
            print (e)

        message_queue.task_done()

#
def aws_client_backup_start():
    aws_client_backup = aws_mqtt_client.AwsMqttClient(config.ADDRESSS_BACKUP, config.PORT_BACKUP, config.USERNAME_BACKUP, config.PASSWORD_BACKUP ,config.SENDTOPIC,config.STATIONTOPIC_BACKUP,True,False,"",config.AWSNAME_BACKUP,config.LOG_FILE,"./config.ini")
    aws_client_backup.message_event += message_handler
    aws_client_backup.connect()
    aws_client_backup.run()
#
thread_insert_database = None
message_queue = queue.Queue()

thread_save_error_data = None
message_error_queue = queue.Queue()

config = aws_utils.config()
config.read_config_file(aws_utils.get_environment("AWS_CONFIG","./config_dev_tckttv.ini"))

aws_client = aws_mqtt_client.AwsMqttClient(config.ADDRESSS, config.PORT, config.USERNAME, config.PASSWORD ,config.SENDTOPIC,config.GETTOPIC,True,False,"",config.AWSNAME,config.LOG_FILE,"./config.ini")
aws_client.message_event += message_handler
aws_client.connect()

datadriver = mongodriver.mongodriver(uri=config.DATABASE_IP, database_name=config.DATABASE_NAME, replicaSet=config.DATABASE_REPLICASET, user_name=config.DATABASE_USER, password=config.DATABASE_PASS, logfile = config.LOG_FILE)
#Start thread
thread_insert_database = threading.Thread(target=insert_database)
thread_insert_database.start()
# aws_client_backup_start
thread_aws_client_backup = threading.Thread(target=aws_client_backup_start)
thread_aws_client_backup.start()
#loop forver
aws_client.run()
#while True:
    #sleep(1.0)


