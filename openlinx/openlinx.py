
#RSLogix Data Logger
from tkinter import *
from pycomm3 import LogixDriver
import pyodbc 
import datetime
import time
import schedule
import threading
import configparser
import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

def readConfig():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
    except:
        log.exception('Config parsing error.')
    else:
        log.info("Config parsed.")
        return config

def connectToDb(dbDriver, dbServer, dbDB):
    try:
        conn = pyodbc.connect('Driver=' + dbDriver + ';'
                              'Server='+ dbServer +';'
                              'Database=' + dbDB + ';'
                              'Trusted_Connection=yes;')
    except:
        log.exception('DB connection error.')
    else:
        log.info("Connected to DB.")
        return conn

def connectToPlc(ipAddress):
    try:
        myPlc = LogixDriver(ipAddress)
    except:
        log.exception('PLC connection error.')
    else:
        log.info("Connected to PLC.")
        return myPlc

def readAndLog(plc, conn, tagList):
    try:
        for tagName in tagList:
            tagData = readTags(plc, tagName)

            #set up sql statement
            currentDate = datetime.datetime.now()
            sqlcmd =    ('INSERT INTO testdb.dbo.tagSamples' 
                         '(tagName, tagValue, sampleDateTime)'
                         ' VALUES (\'' + tagData.tag + '\','+ str(tagData.value) +','
                         '\'' + currentDate.strftime("%Y-%m-%d %H:%M:%S.000") + '\''
                         ')')
            cursor = conn.cursor()
            cursor.execute(sqlcmd)
        conn.commit()
    except:
        log.exception('Error logging.')
    else:
        log.info("Read from PLC & DB Write sucessful")

def readTags(plc, tagName):
    try:
        tagValue = plc.read(tagName)
    except:
        log.exception("Error reading tag: '%s'",tagName)
        return -1;
    else:
        log.info("Tag: '%s' read OK.", tagName)
        return tagValue

def main():
    config = readConfig()
    ipAddress = config['PLCLOG']['ip']
    tagList = config['PLCLOG']['taglist'].split(',')
    dbDriver = config['DBLOG']['driver']
    dbServer = config['DBLOG']['server']
    dbDB = config['DBLOG']['database']
    samplePeriod = int(config['PLCLOG']['period']) #sample period in seconds
    heartbeatPeriod = int(config['DEFAULT']['heartbeat']) 

    dbConn = connectToDb(dbDriver, dbServer, dbDB)
    myPlc = connectToPlc(ipAddress)

    schedule.every(samplePeriod).seconds.do(readAndLog, plc = myPlc, conn = dbConn, tagList = tagList)
    #schedule.every(heartbeatPeriod).seconds.do(plcHeart, plc = myPlc)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            break 

# main function calling 
if __name__=="__main__":      
    main() 