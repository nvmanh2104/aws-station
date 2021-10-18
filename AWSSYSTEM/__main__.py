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
try:
    import queue
except ImportError:
    import Queue as queue

def write_data_to_file(obj, message):
     try:
        station_id = obj["sID"]
        dt = obj['DT']
        file_path = os.path.join(config.FILE_FOLDER, str(dt.year))
        file_path = os.path.join(file_path, str(dt.month))
        file_path = os.path.join(file_path, str(dt.day))
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = "%s_%d%02d%02d%02d%02d%02d.txt"%(station_id, dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        file_name = os.path.join(file_path, file_name)

        file = open(file_name,"w")
        msgtr = json.dumps(message)
        file.write(msgtr)
        file.close()
     except Exception as e:
        log.error("write data to file: %s" %e)

def write_data_to_log(msg):
     try:
        dt = datetime.datetime.now()
        dt = aws_utils.get_datetim_vn_zone(dt)
        file_path = os.path.join(config.DATA_FOLDER, str(dt.year))
        file_path = os.path.join(file_path, str(dt.month))        
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = "%d%02d%02d%02d%02d%02d_%f.txt"%(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, time.clock())
        file_name = os.path.join(file_path, file_name)

        file = open(file_name,"wb")       
        file.write(msg.payload)
        file.close()
     except Exception as e:
        log.error("write data to file: %s" %e)

def write_error_data_to_file(msg):
    try:
        dt = datetime.datetime.now()
        dt = aws_utils.get_datetim_vn_zone(dt)
        file_path = os.path.join(config.DATA_ERROR_FOLDER, str(dt.year))
        file_path = os.path.join(file_path, str(dt.month))
        file_path = os.path.join(file_path, str(dt.day))
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = "%d%02d%02d%02d%02d%02d_%f.txt"%(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, time.clock())
        file_name = os.path.join(file_path, file_name)

        file = open(file_name,"wb")       
        file.write(msg)
        file.close()
    except Exception as e:
        log.error("write data to file: %s" %e)

def write_reponse_timming_to_file(msg):    
    try:
        dt = datetime.datetime.now()
        dt = aws_utils.get_datetim_vn_zone(dt)
        file_path = os.path.join(config.TIMMING_FOLDER, str(dt.year))
        file_path = os.path.join(file_path, str(dt.month))
        file_path = os.path.join(file_path, str(dt.day))
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = "%d%02d%02d%02d%02d%02d_%f.txt"%(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, time.clock())
        file_name = os.path.join(file_path, file_name)

        file = open(file_name,"wb")       
        file.write(msg)
        file.close()
    except Exception as e:
        log.error("write data to file: %s" %e)

def message_handler(sender, msg):
    # write data into queue 
    message_queue.put_nowait(msg)

def error_handler(msg):
    message_error_queue.put_nowait(msg)

#
def test_mqtt_message():
    try:
        file = open("E:\\data\\7\\20\\20210720081107_1186.400556.txt","rb")       
        payload = file.read()
        file.close()
        msg = MQTTMessage("","")
        msg.dup = False
        msg.retain = True
        msg.payload = payload
        return msg
    except Exception as e:
        print(e)
        return None

# process rain
def process_rain(message):
    # process data
    date_time_str = message["DT"]
    #print (date_time_str)
    date_time_obj = datetime.datetime.strptime(date_time_str, '%y-%m-%dT%H:%M:%S')
    #date_time_VN = aws_utils.get_datetim_vn_zone(date_time_obj)
    tz = datetime.timezone(datetime.timedelta(hours=+7), 'Asia/Ho_Chi_Minh')
    date_time_VN = date_time_obj.replace(tzinfo=tz)
    data = {
        "sID": message["sID"],
        "DT": date_time_VN,                
        "rn_10": message["rn_10"],
        "rn_60": message["rn_60"],
        "rn_total":message["rn_total"],
        "bt": message["bt"]
    }
    #write message to file
    write_data_to_file(data, message)
    #write data into MongoDB
    #10m
    data10 = aws_utils.mapping_aws10_to_jica_database(data)
    result = datadriver.insert_data_rain10(data10)
    if result is None:
        log.info("Insert rain data err: %s", result)
    #1h
    minute = date_time_VN.minute
    if minute >= 0 and minute < 6:
        data60 = aws_utils.mapping_aws60_to_jica_database(data)
        result = datadriver.insert_data_rain60(data60)
        if result is None:
            log.info("Insert rain data error: %s", result)

#process water level
def process_waterlevel(message):
    orginal_value = message['value']
    if orginal_value.find('?') > -1 or orginal_value.find('>') > -1:
        values = orginal_value[0:9]
        value = values.split(',')[0]
        message['value'] = aws_utils.convert_feet_to_cm(float(value))
    # process data
    date_time_str = message["DT"]
    #print (date_time_str)
    date_time_obj = datetime.datetime.strptime(date_time_str, '%y-%m-%dT%H:%M:%S')
    #date_time_VN = aws_utils.get_datetim_vn_zone(date_time_obj)
    tz = datetime.timezone(datetime.timedelta(hours=+7), 'Asia/Ho_Chi_Minh')
    date_time_VN = date_time_obj.replace(tzinfo=tz)    
    data = {
        "sID": message["sID"],
        "DT": date_time_VN,                
        "value": message["value"],
        "bt": message["bt"]
    }
    #write message to file
    write_data_to_file(data, message)
    #write data into MongoDB
    #10m
    insert_data = aws_utils.mapping_awsvalue_to_database(data)
    result = datadriver.insert_data_waterlevel(insert_data)
    if result is None:
        log.info("Insert waterlevel data error: %s", result)   
#
def insert_database():
    while True:
        msg = message_queue.get()
        #print( "topic:%s, qos:%s, dup:%s, retain:%s, message:%s"%(msg.topic, str(msg.qos), str(msg.dup), str(msg.retain), msg.payload))        
        #write data to log
        write_data_to_log(msg)

        dup = msg.dup
        retain = msg.retain
        if dup:
           continue
        
        message = aws_utils.decode_payload(msg.payload)        
        if message is None:
            error_handler(msg.payload)
            message = aws_utils.decode_error_payload(msg.payload)
            if message is None:
                continue 
        try:
            # check if request timming syc
            if message.__contains__("RT"):
                timming = aws_utils.get_respone_time_server(message["sID"])                
                aws_client.publish(aws_client.sendtopic, timming)
                write_reponse_timming_to_file(timming)
                continue
            #check and set correct the minute of datetime
            message = aws_utils.correct_time(message)
            #
            if message.__contains__("ss"):
                if message['ss'] == 99:
                    process_waterlevel(message)
            else:
                # process default rain data
                process_rain(message)

            if False:
                # process data
                date_time_str = message["DT"]
                #print (date_time_str)
                date_time_obj = datetime.datetime.strptime(date_time_str, '%y-%m-%dT%H:%M:%S')
                #date_time_VN = aws_utils.get_datetim_vn_zone(date_time_obj)
                tz = datetime.timezone(datetime.timedelta(hours=+7), 'Asia/Ho_Chi_Minh')
                date_time_VN = date_time_obj.replace(tzinfo=tz)
                data = {
                    "sID": message["sID"],
                    "DT": date_time_VN,                
                    "rn_10": message["rn_10"],
                    "rn_60": message["rn_60"],
                    "rn_total":message["rn_total"],
                    "bt": message["bt"]
                }
                #write message to file
                write_data_to_file(data, message)
                #write data into MongoDB
                #10m
                data10 = aws_utils.mapping_aws10_to_jica_database(data)
                result = datadriver.insert_data_rain10(data10)
                if result is not None:
                    log.info("Insert data sucessfully: %s", result)
                #1h
                minute = date_time_VN.minute
                if minute >= 0 and minute < 6:
                    data60 = aws_utils.mapping_aws60_to_jica_database(data)
                    result = datadriver.insert_data_rain60(data60)
                    if result is not None:
                        log.info("Insert data sucessfully: %s", result)

        except Exception as e:
            log.error("insert_database: %s" %e)
            print (e)

        message_queue.task_done()

def save_error_data_file():
    while True:
        msg = message_error_queue.get()
        write_error_data_to_file(msg)
        message_error_queue.task_done()

#
thread_insert_database = None
message_queue = queue.Queue()

thread_save_error_data = None
message_error_queue = queue.Queue()

config = aws_utils.config()
config.read_config_file(aws_utils.get_environment("AWS_CONFIG","./config_dev_tckttv.ini"))
#aws_client = paho_emqtt_aws.EmqttAWS(config.ADDRESSS, config.PORT, config.USERNAME, config.PASSWORD ,config.SENDTOPIC,config.GETTOPIC,True,False,"",config.AWSNAME,config.LOG_FILE,"./config.ini")
aws_client = aws_mqtt_client.AwsMqttClient(config.ADDRESSS, config.PORT, config.USERNAME, config.PASSWORD ,config.SENDTOPIC,config.GETTOPIC,True,False,"",config.AWSNAME,config.LOG_FILE,"./config.ini")
aws_client.message_event += message_handler
aws_client.connect()

# test send message
#testmessage = test_mqtt_message()
#aws_client.publish(aws_client.gettopic, testmessage.payload)
# test data message
#msg = test_mqtt_message()
#message_queue.put_nowait(msg)


env = aws_utils.get_environment("AWS_ENV","dev")
if env == "dev":
    #datadriver = mongodriver.mongodriver(uri=config.DATABASE_IP, database_name=config.DATABASE_NAME, user_name=config.DATABASE_USER, password=config.DATABASE_PASS, logfile = config.LOG_FILE)
    datadriver = mongodriver.mongodriver(uri=config.DATABASE_IP, database_name=config.DATABASE_NAME, replicaSet=config.DATABASE_REPLICASET, user_name=config.DATABASE_USER, password=config.DATABASE_PASS, logfile = config.LOG_FILE)
else:
    #datadriver = mongodriver.mongodriver(uri=config.DATABASE_IP, database_name=config.DATABASE_NAME, replicaSet=config.DATABASE_REPLICASET, tls=True, tlsCAFile=config.CA_FILE, tlsCertificateKeyFile=config.CERT_FILE, logfile=config.LOG_FILE)
    datadriver = mongodriver.mongodriver(uri=config.DATABASE_IP, database_name=config.DATABASE_NAME, replicaSet=config.DATABASE_REPLICASET, user_name=config.DATABASE_USER, password=config.DATABASE_PASS, logfile = config.LOG_FILE)

#
log = logging.getLogger(__name__ + '.EmqttAWS')
hdlr = logging.FileHandler(config.LOG_FILE)
# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# hdlr.setFormatter(formatter)
log.addHandler(hdlr)
#Start thread
thread_insert_database = threading.Thread(target=insert_database)
thread_insert_database.start()

thread_save_error_data = threading.Thread(target=save_error_data_file)
thread_save_error_data.start()
#
#loop forver
aws_client.run()
#while True:
    #sleep(1.0)


