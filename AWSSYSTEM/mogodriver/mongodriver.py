from pymongo import MongoClient,ReadPreference
import logging
from datetime import datetime, timedelta
import pytz
from utils import aws_utils

class mongodriver (object):
    mongoclient = None
    database = None
    status = None
    def __init__(self, uri="192.168.1.150:27017", database_name='aws', user_name='', password='', replicaSet='', tls=False, tlsCAFile='', tlsCertificateKeyFile='' ,logfile="./aws.log"):
         #
        self.log = logging.getLogger(__name__ + '.EmqttAWS')
        self.hdlr = logging.FileHandler(logfile)
        self.log.addHandler(self.hdlr)

        mongodriver.mongoclient = MongoClient(uri, replicaSet=replicaSet, username=user_name, password=password, authMechanism='SCRAM-SHA-1')
        mongodriver.database = mongodriver.mongoclient[database_name]
       
    def check_status (self):
        stt = mongodriver.database.command('serverStatus')
        if stt is not None:
            mongodriver.status = True
            return True
        else:
            mongodriver.status = False
            return False
            
    def insert_user_password(self, data):
        collection = mongodriver.database.mqtt_user
        
        query = {"username": data["username"]}

        return collection.replace_one(query, data, upsert=True)

        
