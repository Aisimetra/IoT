# python 3.6

import random
import time
from datetime import datetime
from queue import Queue

from paho.mqtt import client as mqtt_client
from flask import Flask, render_template, request
import re
import json
from flask_mysqldb import MySQL

q = Queue()

app = Flask(__name__)
# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'
messages = []

# My sql
# da modificare
app.config['MYSQL_HOST'] = '149.132.178.180'
app.config['MYSQL_USER'] = 'asarteschi'
app.config['MYSQL_PASSWORD'] = 'iot829677'
app.config['MYSQL_DB'] = 'asarteschi'
app.config['MYSQL_DATABASE_PORT'] = 3306
mysql = MySQL(app)
temperature = 0.0
real_temperature = 0.0
humidity = 0.0
fire = False
proximity = False


# HTML
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/confirm', methods=['POST'])
def my_form_post():
    mac = request.form['slave']
    prod = request.form.get("Prod")
    stoc = request.form.get("Stoc")
    mac_validation = bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})'] * 6) + '$', mac.lower()))

    if not mac_validation:
        return render_template('error.html', utc_dt="L'indirizzo MAC inserito è errato ")

    client = connect_mqtt()
    publish(client, mac)
    subscribe(client)
    client.loop_start()

    return render_template('confirm.html', title="stoccaggio", conf="lo stoccaggio")


@app.route('/new_node')
def index_page():
    return render_template('new_node.html')


@app.route('/home_con_Sensori')
def hom_sens():
    # ho già fatto la connection quidni ho i dati
    # chiamo il parsing
    pd()
    # da sistemare
    return render_template('home_con_Sensori.html')


def pd(last_dato):  # parsing divino
    string_parse = json.loads(last_dato)
    if string_parse['id'] == 'production' and string_parse['priority'] == 'low':
        temperature = str(string_parse['temperature'])
        real_temperature = str(string_parse['real_temperature'])
        humidity = str(string_parse['humidity'])
        print('production low')
        mysql_connection_insert(temperature,real_temperature,humidity)
    elif string_parse['id'] == 'production' and string_parse['priority'] == 'high':
        fire = string_parse['fire']
        proximity = string_parse['proximity']
        print('production high ')
        mysql_connection_insert()
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high':
        fire = string_parse['fire']
        proximity = string_parse['proximity']
        print('priority high ')
        mysql_connection_insert()
    else:
        print('Si è rotto ')


def subscribe(client: mqtt_client):
    def on_message(client, userdata, message):
        # print(f"Recived `{m}` from topic `{topic}`")
        messages.append(str(message.payload.decode("utf-8")))
        conf = json.loads(messages[-1])

        if conf['id'] == 'confirm':
            topic_l = conf['topic_l']
            topic_h = conf['topic_h']
            client.loop_start()
            client.subscribe(topic_l)
            client.subscribe(topic_h)
            q = str(message.payload.decode("utf-8"))
            print(' ' + q)
        if len(messages) >= 2:
            print(messages[-1])
            pd(messages[-1])
        return None

    client.subscribe(topic)
    client.on_message = on_message


@app.route("/", methods=['GET','POST'])
def mysql_connection_insert(temperature,real_temperature,humidity):
    with app.app_context():
        cursor = mysql.connection.cursor()
    #if tipe == 'production' and priority == 'low':
        cursor.execute(''' INSERT INTO asarteschi.production_low VALUES(%s,%s,%s,%s)''', (len(messages), temperature, real_temperature, humidity))
    # elif tipe == 'production' and priority == 'high':
    #     cursor.execute(''' INSERT INTO production_high VALUES(%d,%d)''', (fire, proximity))
    # elif tipe == 'storage' and priority == 'high':
    #     cursor.execute(''' INSERT INTO storage_high VALUES(%d,%d)''', (fire, proximity))
        mysql.connection.commit()
        cursor.close()


@app.route('/sensor')
def sensor_page():
    return render_template('sensor.html')


# MQTT
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            connected = True
            print("Connected to MQTT Broker!")
        else:
            connected = False
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, mac):
    msg = json.dumps({"id": "invite", "mac": mac}, sort_keys=True, indent=4)
    result = client.publish(topic, msg)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def run():
    index()


if __name__ == '__main__':
    # run()
    app.run(debug=True, host='127.0.0.1')
