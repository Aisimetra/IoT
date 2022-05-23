# python 3.6

import random
import time
from queue import Queue

from paho.mqtt import client as mqtt_client
from flask import Flask, render_template, request
import re
import json

q = Queue()
from flask_mysqldb import MySQL

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
app.config['MYSQL_DB'] = 'flask'

mysql = MySQL(app)


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

    # if len(messages) == 2 :
    #     conf = json.loads(messages[1])
    #     if conf['id'] == 'confirm' and conf['mac'] == '80:7D:3A:42:EF:6A':
    #        title = 'stoccaggio'
    #     else
    #       title = 'produzione'
    return render_template('confirm.html', title="stoccaggio", conf="lo stoccaggio")


@app.route('/new_node')
def index_page():
    return render_template('new_node.html')


@app.route('/home_con_Sensori')
def hom_sens():
    # poi capisco come farlo
    topic = 'gmadotto1/production/low_priority'
    # da sistemare
    connect_mqtt()
    # da sistemare
    pd()
    # da sistemare
    mysql_connection()
    return render_template('home_con_Sensori.html')


def pd(last_dato):  # parsing divino
    string_parse = json.loads(last_dato)
    if string_parse['che topic è']: #
        save = 'topic che indicherà dove salvare'
        if string_parse['temperatura']:
            salvo = 'inserisco la temperature'
    print('passo poi a mysql')


# @app.route('/login', methods = ['POST', 'GET'])
def mysql_connection():
    cursor = mysql.connection.cursor()
    name = 89  # cose estatte con il parsing
    # da inserire le query
    cursor.execute(''' INSERT INTO info_table VALUES(%s,%s)''', (name, age))

    # Saving the Actions performed on the DB
    mysql.connection.commit()

    # Closing the cursor
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


def subscribe(client: mqtt_client):
    def on_message(client, userdata, message):
        m = str(message.payload.decode("utf-8"))
        messages.append(m)
        pd(m)
        if len(messages) == 2:
            conf = json.loads(messages[1])
            if conf['id'] == 'confirm':
                print('subscribe')
            return client.loop_stop()

    client.subscribe(topic)
    client.on_message = on_message


def run():
    index()


if __name__ == '__main__':
    # run()
    app.run(debug=True, host='127.0.0.1')
