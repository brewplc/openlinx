
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


###FUNCTIONS####
def readConfig():
    try:
        config = configparser.ConfigParser()
        config.read('config.ini')
    except:
        log.exception('Config parsing error.')
    else:
        log.info("Config parsed.")
        return config

def connectToDb():
    try:
        conn = pyodbc.connect('Driver={SQL Server};'
                              'Server=MANUF-MITCH-NB\SQLEXPRESS;'
                              'Database=testdb;'
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

def createUI():
    def startBtnClick():
        statusLbl1.configure(text="Logging begins in 4 seconds.")
        time.sleep(5)
        window.destroy()


    window = Tk()
    window.title("Logix Log")

    startBtn = Button(window, text="Accept", command = startBtnClick, width = 20)
    startBtn.grid(column=0, row=3)

    statusLbl1 = Label(window, text="Select tags and click Accept.", font=("Arial Bold", 10))
    statusLbl1.grid(column=0, row=1)

    tagListFrame = Frame(window)
    tagListFrame.grid(column=0, row=2, columnspan = 3)

    tagList = Listbox(tagListFrame)
    tagList.pack(side = 'left', fill = 'y')
    tagList.insert(1,'tag1')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(2,'tag2')
    tagList.insert(3,'tag3')
    tagList.insert(4,'tag4')
    tagList.insert(5,'tag5')

    scrollbar = Scrollbar(tagListFrame, orient="vertical", command=tagList.yview)
    scrollbar.pack(side = "right", fill = "y")

    window.geometry('400x400')
    window.mainloop()

###MAIN###
def main():
    config = readConfig()
    ipAddress = config['PLCLOG']['ip']
    tagList = config['PLCLOG']['taglist'].split(',')

    dbConn = connectToDb()
    myPlc = connectToPlc(ipAddress)
    samplePeriod = int(config['PLCLOG']['period']) #sample period in seconds
    heartbeatPeriod = int(config['DEFAULT']['heartbeat']) 

    schedule.every(samplePeriod).seconds.do(readAndLog, plc = myPlc, conn = dbConn, tagList = tagList)
    schedule.every(heartbeatPeriod).seconds.do(plcHeart, plc = myPlc)

    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except KeyboardInterrupt:
            break 

# main function calling 
if __name__=="__main__":      
    main() 