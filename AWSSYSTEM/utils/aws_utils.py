from datetime import datetime
import logging
import os
import json
import time
import pytz
import re

try:
    import configparser
except:
    from six.moves import configparser

def correct_time(message):
    dt = datetime.strptime(message['DT'], '%y-%m-%dT%H:%M:%S')
    minute = round(dt.minute/10)*10
    dt = dt.replace(minute=minute)
    message['DT'] = dt.strftime('%y-%m-%dT%H:%M:%S')
    return message
# convert feet to cm
def convert_feet_to_cm(feet):
    return feet * 1

# Ten file: VinaRain_yyyyMMddHHmmss.txt
def get_filename_string():
    dt = datetime.now()
    dt = get_datetim_vn_zone(dt)
    filename = "_" + str(dt.year)
    filename +=  str((dt.month)) if dt.month > 9 else ("0"+str((dt.month)))
    filename += str((dt.day)) if dt.day > 9 else ("0" + str((dt.day)))
    filename += str((dt.hour)) if dt.hour > 9 else ("0" + str((dt.hour)))
    filename += str((dt.minute)) if dt.minute > 9 else ("0" + str((dt.minute)))
    filename += str((dt.second)) if dt.second > 9 else ("0" + str(dt.second))
    return filename

def get_datetim_vn_zone(datetime_zone):
    time_zone_VN = pytz.timezone('Asia/Ho_Chi_Minh')
    datetime_vn = datetime_zone.astimezone(time_zone_VN)
    return datetime_vn

def get_respone_time_server(stationID):
    now =  datetime.now()
    currentDatetime = get_datetim_vn_zone(now)
    #print currentDatetime
    data = {"sID":stationID,"RT":"T_RES","T":{"H":currentDatetime.hour,"M":currentDatetime.minute,"S":currentDatetime.second},"D":{"D":currentDatetime.day,"M":currentDatetime.month,"Y":currentDatetime.year}}
    data_json = json.dumps(data)
    data_response = data_json.encode('utf-8')
    return data_response

def decode_payload(payload):
    '''
    Format json for pretty printing, return string sutiable for logging,
    and a dict of the json data
    '''
    indent = 31 #number of spaces to indent json data
    json_data = ""
    try:
        # if it's json data, decode it (use OrderedDict to preserve keys
        # order), else return as is...
        payload = payload.decode()
        payload_ascii = ""
        for ch in payload:
            if ord(ch) >= 33 and ord(ch) <= 126:
                payload_ascii += ch   

        json_data = ""        
        json_data = json.loads(
            payload_ascii.replace(":nan", ":NaN").\
            replace(":inf", ":Infinity").replace(":-inf", ":-Infinity"))
        # if it's not a dictionary, probably just a number
        if not isinstance(json_data, dict):
            return json_data, dict(json_data)
        json_data_string = "\n".join((indent * " ") + i for i in \
            (json.dumps(json_data, indent = 2)).splitlines())

        formatted_data = "Decoded JSON: \n%s" % (json_data_string)

    except: #ValueError:
        #json_data = payload
        print ("error in decode_payload method \r\n")
        return None

    #return formatted_data, dict(json_data)
    return  dict(json_data)

def decode_error_payload(payload):
    try:
        data_arr = []
        for i in range(0, len(payload)-4):
            ch = payload[i]
            if ch >= 23 and ch <= 126:
                data_arr.append(chr(ch))
        
        if len (data_arr) >0 :
            data_str = ''.join(data_arr)   
            data_str = data_str.replace('"','')
            data_list = data_str.split(',')
            data = {}
            for dt in data_list:
                if dt.find('DT') != -1:
                    pattern = ':'
                    result = re.split(pattern, dt, 1) 
                    if len(result) == 2:
                        data['DT'] = result[1]
                else:
                    key_value = dt.split(':')
                    if len(key_value) == 2:
                        key = key_value[0].replace('{','').replace('}','')
                        value = key_value[1].replace('{','').replace('}','')
                        if key != 'sID':
                            data[key] = float(value)
                        else:
                            data[key] = value
            
            if not 'rn_total' in data:
                data['rn_total'] = -999
            if not 'bt' in data:
                data['bt'] = 94            
            #data_json = decode_payload(data.encode("utf-8"))
            return data        
    except Exception as ex:
        print(ex)
        return None

def mapping_aws10_to_jica_database(data):
    now = datetime.now()
    now = get_datetim_vn_zone(now)
    res_data = {
        'StationID': data['sID'],
        'DateTime': data['DT'],
        'Value': data['rn_10'],
        'Rain60': data['rn_60'],
        'RainTotal': data['rn_total'],
        'Battery': data['bt'],
        'CreatedTime': now,
        'UpdatedTime': now,
        }
    return res_data

def mapping_awsvalue_to_database(data):
    now = datetime.now()
    now = get_datetim_vn_zone(now)
    res_data = {
        'StationID': data['sID'],
        'DateTime': data['DT'],
        'Value': data['value'],        
        'Battery': data['bt'],
        'CreatedTime': now,
        'UpdatedTime': now,
        }
    return res_data

def mapping_aws60_to_jica_database(data):
    now = datetime.now()
    now = get_datetim_vn_zone(now)
    res_data = {
        'StationID': data['sID'],
        'DateTime': data['DT'],
        'Value': data['rn_60'],
        'RainTotal': data['rn_total'],
        'CreatedTime': now,
        'UpdatedTime': now,
        }
    return res_data

def get_environment(variable, default_return):
    evn_value = os.environ.get(variable, default_return)
    return evn_value

class config (object):
    AWSNAME = "AWS"
    ADDRESSS = "101.96.116.76"
    PORT = 1883
    SENDTOPIC = "aws/senddata"
    GETTOPIC = "aws/getdata"
    ROOT_FOLDER = "D:\\"
    FILE_FOLDER = "D:\\files"
    DATA_FOLDER = "D:\\data"
    DATA_ERROR_FOLDER = "D:\\data_error"
    LOG_FOLDER = "D:\\log"
    TIMMING_FOLDER = "D:\\timming"
    LOG_FILE = "aws.log"
    DATABASE_IP = "192.168.1.71"
    DATABASE_NAME = "aws"
    DATABASE_PORT = 14680
    DATABASE_USER = "ai"
    DATABASE_PASS = "ai@0258"
    DATABASE_NAME_VIEW = ""
    DATABASE_REPLICASET= ""
    CA_FILE = ""
    CERT_FILE = ""

    USERNAME = ""
    PASSWORD = ""
    
    def __init__(self, logfile="./aws.log"):
        self.log = logging.getLogger(__name__ + '.EmqttAWS')
        self.hdlr = logging.FileHandler(logfile)
        # formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        # hdlr.setFormatter(formatter)
        self.log.addHandler(self.hdlr)

    def read_config_file(self, file="./config.ini"):
        #read config file
        conf = configparser.ConfigParser()
        try:
            conf.read(file)
        except Exception as e:
            self.log.warn("Error reading config file %s" %e)
            self.log.info("No Roomba specified, and no config file found - "
                          "attempting discovery")
            return False
        self.log.info("reading info from config file %s" % file)
        # get config
        config.ADDRESSS = conf.get("Emqtt","ADDRESSS")
        config.AWSNAME = conf.get("Emqtt","AWSNAME")
        config.PORT = int(conf.get("Emqtt", "PORT"))
        config.SENDTOPIC = conf.get("Emqtt", "SENDTOPIC")
        config.GETTOPIC = conf.get("Emqtt", "GETTOPIC")
        config.USERNAME = conf.get("Emqtt", "USERNAME")
        config.PASSWORD = conf.get("Emqtt", "PASSWORD")
        
        #emqtt backup
        config.ADDRESSS_BACKUP = conf.get("Emqtt_Backup","ADDRESSS")
        config.AWSNAME_BACKUP = conf.get("Emqtt_Backup","AWSNAME")
        config.PORT_BACKUP = int(conf.get("Emqtt_Backup", "PORT"))
        config.STATIONTOPIC_BACKUP = conf.get("Emqtt_Backup", "STATIONTOPIC")
        config.USERNAME_BACKUP = conf.get("Emqtt_Backup", "USERNAME")
        config.PASSWORD_BACKUP = conf.get("Emqtt_Backup", "PASSWORD")
        
        config.DATABASE_IP = conf.get("Database", "DATABASE_IP")       
        config.DATABASE_NAME = conf.get("Database", "DATABASE_NAME")
        config.DATABASE_USER = conf.get("Database", "DATABASE_USER")
        config.DATABASE_PASS = conf.get("Database", "DATABASE_PASS")
        config.DATABASE_NAME_VIEW = conf.get("Database", "DATABASE_NAME_VIEW")
        config.DATABASE_REPLICASET = conf.get("Database", "DATABASE_REPLICASET")        
   
        config.FILE_FOLDER = conf.get("Paths", "FILE_FOLDER")
        config.DATA_FOLDER = conf.get("Paths", "DATA_FOLDER")
        config.LOG_FOLDER = conf.get("Paths", "LOG_FOLDER")
        config.TIMMING_FOLDER = conf.get("Paths", "TIMMING_FOLDER")
        config.LOG_FILE = os.path.join(config.LOG_FOLDER,"aws.log")
        config.DATA_ERROR_FOLDER = conf.get("Paths", "DATA_ERROR_FOLDER")


        if not os.path.exists(config.LOG_FOLDER):
            os.mkdir(config.LOG_FOLDER)
        if not os.path.exists(config.FILE_FOLDER):
            os.mkdir(config.FILE_FOLDER)
        if not os.path.exists(config.LOG_FILE):
            file = open(config.LOG_FILE,"w")
            file.close()
        return True
