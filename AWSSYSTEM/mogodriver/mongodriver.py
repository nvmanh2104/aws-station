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

        env = aws_utils.get_environment("AWS_ENV","dev")
        if env == "dev":
            #mongodriver.mongoclient = MongoClient(uri, username=user_name, password=password, authMechanism='SCRAM-SHA-1')
            mongodriver.mongoclient = MongoClient(uri, replicaSet=replicaSet, username=user_name, password=password, authMechanism='SCRAM-SHA-1')
        else:
            #mongodriver.mongoclient = MongoClient(uri, replicaSet=replicaSet, tls=tls, tlsCAFile=tlsCAFile, tlsCertificateKeyFile=tlsCertificateKeyFile, tlsAllowInvalidCertificates=True)
            mongodriver.mongoclient = MongoClient(uri, replicaSet=replicaSet, username=user_name, password=password, authMechanism='SCRAM-SHA-1')
        
        mongodriver.database = mongodriver.mongoclient[database_name]#mongodriver.mongoclient.VNMHAAWS        
       
    def check_status (self):
        stt = mongodriver.database.command('serverStatus')
        if stt is not None:
            mongodriver.status = True
            return True
        else:
            mongodriver.status = False
            return False
    def insert_data_rain10(self, data):
        collection = mongodriver.database.rain10m
        #collection = mongodriver.database.test
        #fromDate = data["DateTime"] + timedelta(minutes=-1)
        #toDate = data["DateTime"] + timedelta(minutes=1)
        #query = {"DateTime": {"$gte": fromDate, "$lt": toDate}, "StationID": data["StationID"]}

        query = {"DateTime": data["DateTime"], "StationID": data["StationID"]}

        return collection.replace_one(query, data, upsert=True)

        #if table.find(query).count() == 0:
        #    return table.insert_one(data)
        #return None

    def insert_data_rain60(self, data):       
        collection = mongodriver.database.rain1h
        #collection = mongodriver.database.test1h
        #fromDate = data["DateTime"] + timedelta(minutes=-1)
        #toDate = data["DateTime"] + timedelta(minutes=1)
        #query = {"DateTime": {"$gte": fromDate, "$lt": toDate}, "StationID": data["StationID"]}
        
        query = {"DateTime": data["DateTime"], "StationID": data["StationID"]}
        return collection.replace_one(query, data, upsert=True)

        #if table.find(query).count() == 0:
        #    return table.insert_one(data)
        #return None

    def insert_data_waterlevel(self, data):
        collection = mongodriver.database.waterlevel10m        

        query = {"DateTime": data["DateTime"], "StationID": data["StationID"]}

        return collection.replace_one(query, data, upsert=True)
        

if __name__ == '__main__':
    
    dt = datetime.now()

    data = {
        'StationID': '123456',
        'DateTime': dt,
        'value': 10,
        }
    datadriver = mongodriver('192.168.1.71:14680', 'aws-taynguyen', 'ai', 'ai@0258', 'mongodb')
    datadriver.insert_data_rain10(data)
    datadriver.insert_data_rain10(data)
    datadriver.insert_data_rain60(data)
    datadriver.insert_data_rain60(data)