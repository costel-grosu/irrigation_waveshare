from gpiozero import LED
from time import sleep

from paho.mqtt import client as mqtt_client

#import context  # Ensures paho is in PYTHONPATH

import logging
import re
import sys


# gpiozero https://gpiozero.readthedocs.io/en/stable/api_output.html
# paho.mqtt https://www.eclipse.org/paho/index.php?page=clients/python/index.php



from logging.handlers import TimedRotatingFileHandler
FORMATTER = logging.Formatter("%(asctime)s — %(name)s — %(levelname)s — %(message)s")
LOG_FILE = "irrigation.log"

def get_console_handler():
   console_handler = logging.StreamHandler(sys.stdout)
   console_handler.setFormatter(FORMATTER)
   return console_handler
def get_file_handler():
   file_handler = TimedRotatingFileHandler(LOG_FILE, when='midnight')
   file_handler.setFormatter(FORMATTER)
   return file_handler
def get_logger(logger_name):
   logger = logging.getLogger(logger_name)
   logger.setLevel(logging.DEBUG) # better to have too much log than not enough
   logger.addHandler(get_console_handler())
   logger.addHandler(get_file_handler())
   # with this pattern, it's rarely necessary to propagate the error up to parent
   logger.propagate = False
   return logger

logging.basicConfig(level=logging.DEBUG)
logger = get_logger("bigbox")
#mqtt_client.enable_logger(logger)


ch1 = LED(5)
ch2 = LED(6)
ch3 = LED(13)
ch4 = LED(16)
ch5 = LED(19)
ch6 = LED(20)

channels = (ch1, ch2, ch3, ch4, ch5, ch6)


broker = '192.168.3.116'
port = 1883
topic = "irrigation/bigbox/+/set"


client_id = f'irrigation_bigbox'
username = 'homeassistant'
password = 'xxx'


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)
    # Set Connecting Client ID
    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, channel, id):
    topic = f"irrigation/bigbox/ch{id}/state"
    msg = "ON" if channel.value == 1 else "OFF"
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Sent `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def publish_all(client):
    for id in range(1, len(channels)+1):
        channel = channels[id-1]
        publish(client, channel, id)


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        pattern = "irrigation/bigbox/ch([1..6]+)/set"
        result = re.search("irrigation/bigbox/ch(\d)/set", msg.topic)
        if result:
            id = int(result.group(1))
            value = 1 if msg.payload.decode() == "ON" else 0
            print(f"channel id: {id} value {value}")
            channel_set(client, id, value)
        else:
            print("does not match")

    client.subscribe(topic)
    client.on_message = on_message

def channel_set(client, id, value):
    if id <= 6:
        channel = channels[id - 1]
        channel.value = value
        logger.info(f"Set Channel:{id} value:{value}")
        if client:
            publish(client, channel, id)



if __name__ == '__main__':

    #test
    ch3.on()
    ch5.on()

    client = connect_mqtt()
    subscribe(client)
    publish_all(client)

    client.loop_forever()
