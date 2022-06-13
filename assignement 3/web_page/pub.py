# python 3.6
import base64
import random
import time
from datetime import datetime
from queue import Queue

from flask_mysqldb import MySQL
from paho.mqtt import client as mqtt_client
from flask import Flask, render_template, request
import re
import json, requests
from flask_mysqldb import MySQL
from telegram import update

app = Flask(__name__)
# from flask_mysqldb import MySQL

q = Queue()

# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
topic_data = "gmadotto1/data"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'
messages = []
MAX_DB_ROWS = 100
nodes = []
max_nodes = 2

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
fire = 0
proximity = 0

# API
BASE_URL = "https://api.openweathermap.org/data/2.5/weather?"
CITY = "Massa"
API_KEY = "3864958da0707c963f5bddd1dbd89882"
URL = BASE_URL + "q=" + CITY + "&appid=" + API_KEY + "&lang=it"

import tkinter as tk

# HTML
@app.route('/')
def index():
    if len(nodes) == 0:
        return render_template('home.html')
    return hom_sens()


@app.route('/gestione_nodi')
def gestione_nodi():
    return render_template('gestione_nodi.html', nodes=nodes)


@app.route('/confirm', methods=['POST'])
def my_form_post():
    mac = request.form['slave']  # sopra
    mac2 = request.form['slave2']  # sotto
    mac_validation = bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})'] * 6) + '$', mac.lower()))
    mac_validation2 = bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})'] * 6) + '$', mac2.lower()))

    if not mac_validation or not mac_validation2:
        # return render_template('error.html', utc_dt="L'indirizzo MAC inserito è errato ")
        return render_template('new_node.html', flag=True)

    client = connect_mqtt()
    publish(client, mac, mac2)
    subscribe(client)
    client.loop_start()
    nodes.append(mac)
    nodes.append(mac2)
    return render_template('confirm.html', title="stoccaggio", conf="lo stoccaggio")


@app.route('/new_node')
def index_page():
    return render_template('new_node.html', flag=False)


def check_sensore_temp(valore):
    if valore == "None":
        return "Sensore non operativo", "label-danger"
    if valore is not None:
        if float(valore) > 24.0:
            return "Temperatura alta, ventole attive", "label-warning"
    return "Tutto ok", "label-success"


def check_sensore_hum(valore):
    if valore == "None":
        return "Sensore non operativo", "label-danger"
    if valore is not None:
        if float(valore) > 70.0:
            return "Umidita' alta, deumidificazione", "label-warning"
    return "Tutto ok", "label-success"


def check_incendio(value):
    if value == "False" or value == "false":
        return "Tranquillo", "badge-success"
    if value == "True" or value == "true":
        return "Incendio", "badge-danger"
    return "Problema al sensore", "badge-warning"


def check_intruso(value):
    if value == "False" or value == "false":
        return "Nessun intruso", "badge-success"
    if value == "True" or value == "true":
        return "Intruso", "badge-danger"
    return "Problema al sensore", "badge-warning"


@app.route('/home_con_Sensori')
def hom_sens():
    alarm_prod = my_sql_connection_select_high_production()
    alarm_storage = my_sql_connection_select_high_storage()
    storage = my_sql_connection_select_low()
    print("alarm prod:", alarm_prod)
    print("alarm storage:", alarm_storage)
    print("sensor storage:", storage)
    CITY, temperature, cloud, wind, iconUrl = api_meteo()
    if not storage:
        storage = (-1, "", -1, -1, -1)

    if not alarm_prod:
        alarm_prod = (-1, "", "", "")

    if not alarm_storage:
        alarm_storage = (-1, "", "", "")

    label_sensore_temp, badge_sensore_temp = check_sensore_temp(storage[2])
    label_sensore_real_temp, badge_sensore_real_temp = check_sensore_temp(storage[3])
    label_sensore_hum, badge_sensore_hum = check_sensore_hum(storage[4])

    incendio_prod, incendio_prod_badge = check_incendio(alarm_prod[2])
    incendio_stoc, incendio_stoc_badge = check_incendio(alarm_storage[2])
    intruso_stoc, intruso_stoc_badge = check_intruso(alarm_storage[3])

    return render_template('home_con_Sensori.html', label1=incendio_prod, badge1=incendio_prod_badge,
                           label2=intruso_stoc, badge2=intruso_stoc_badge, label3=incendio_stoc,
                           badge3=incendio_stoc_badge,
                           temp_v=storage[2], real_temp_v=float("{0:.2f}".format(float(storage[3]))), hum_v=storage[4],
                           temp_ext=temperature, wind_d=wind, cloud_d=cloud, city=CITY,
                           label_sensore_temp=label_sensore_temp, badge_sensore_temp=badge_sensore_temp,
                           label_sensore_real_temp=label_sensore_real_temp,
                           badge_sensore_real_temp=badge_sensore_real_temp,
                           label_sensore_hum=label_sensore_hum, badge_sensore_hum=badge_sensore_hum,
                           IMMAGININA = iconUrl
                           )


# Api meteo
def api_meteo():
    print("api meteo")
    response = requests.get(URL)

    # checking the status code of the request
    if response.status_code == 200:
        # getting data in the json format
        data = response.json()
        # getting the main dict block
        main = data['main']
        # getting temperature
        temperature = float("{0:.2f}".format( main['temp'] - 273.15))
        # weather report
        report = data['weather']
        # wind report
        wind_repo = data['wind']
        iconCode = report[0]['icon']
        print(f"{CITY:-^30}")
        print(f"Temperature: {temperature}")
        cloud = report[0]['description']
        print(f"Weather Report: {cloud}")
        wind_display = wind_repo['speed']
        print(f"Wind Report: {wind_display}")
        iconUrl = "http://openweathermap.org/img/w/" + iconCode + ".png"

    else:
        # showing the error message
        print("Error in the HTTP request")

    return CITY, temperature, cloud, wind_display, iconUrl, iconCode

def check_db_table(table):
    print("table:", table)
    count = None
    with app.app_context():
        cursor = mysql.connection.cursor()
        query = 'SELECT COUNT(*) FROM ' + table
        cursor.execute(query)
        for item in cursor:
            count = item
        mysql.connection.commit()
        cursor.close()
        print("righe presenti:", count[0])

    if count[0] >= MAX_DB_ROWS:
        print("troppi record, svuoto tabella")
        with app.app_context():
            cursor = mysql.connection.cursor()
            query = 'ALTER TABLE ' + table + ' AUTO_INCREMENT = 0;'
            cursor.execute(query)
            mysql.connection.commit()

            query = 'TRUNCATE TABLE ' + table + ';'
            cursor.execute(query)
            mysql.connection.commit()
            cursor.close()


def pd(last_dato):  # parsing divino
    string_parse = json.loads(last_dato)

    check_db_table('asarteschi.production_low')
    check_db_table('asarteschi.production_high')
    check_db_table('asarteschi.storage_high')

    if string_parse['id'] == 'production' and string_parse['priority'] == 'low':
        temperature = str(string_parse['temperature'])
        real_temperature = str(string_parse['real_temperature'])
        humidity = str(string_parse['humidity'])
        # print('production low')
        mysql_connection_insert_low(temperature, real_temperature, humidity)
    elif string_parse['id'] == 'production' and string_parse['priority'] == 'high':
        fire = str(string_parse['fire'])
        proximity = str(string_parse['proximity'])
        # print('production high ')
        mysql_connection_insert_high('production', fire, proximity)
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high':
        fire = str(string_parse['fire'])
        proximity = str(string_parse['proximity'])
        # print('priority high ')
        mysql_connection_insert_high('storage', fire, proximity)
    else:
        print('Si è rotto ')


def subscribe(client: mqtt_client):
    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        messages.append(str(msg.payload.decode("utf-8")))
        conf = json.loads(messages[-1])
        print(messages[-1])
        pd(messages[-1])

    client.subscribe(topic)
    client.subscribe(topic_data)
    client.on_message = on_message


@app.route("/", methods=['GET', 'POST'])
def mysql_connection_insert_low(temperature, real_temperature, humidity):
    with app.app_context():
        cursor = mysql.connection.cursor()
        query = 'INSERT INTO asarteschi.production_low (temperature, real_temperature, humidity) VALUES (%s,%s,%s)'
        cursor.execute(query, [temperature, real_temperature, humidity])
        mysql.connection.commit()
        cursor.close()


@app.route("/", methods=['GET', 'POST'])
def mysql_connection_insert_high(str, flame, proximity):
    with app.app_context():
        cursor = mysql.connection.cursor()
        if str == 'production':
            query = 'INSERT INTO asarteschi.production_high (flame, proximity) VALUES (%s,%s)'
            cursor.execute(query, [flame, proximity])
            mysql.connection.commit()
            cursor.close()
        elif str == 'storage':
            query = 'INSERT INTO asarteschi.storage_high (flame, proximity) VALUES (%s,%s)'
            cursor.execute(query, [flame, proximity])
            mysql.connection.commit()
            cursor.close()


@app.route("/", methods=['GET', 'POST'])
def my_sql_connection_select_low():
    rows = []
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.production_low ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        if not rows == []:
            return rows[0]
        return []


@app.route("/", methods=['GET', 'POST'])
def my_sql_connection_select_high_production():
    rows = []
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.production_high ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        if not rows == []:
            return rows[0]
        return []


@app.route("/", methods=['GET', 'POST'])
def my_sql_connection_select_high_storage():
    rows = []
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.storage_high ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        if not rows == []:
            return rows[0]
        return []


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


def publish(client, mac, mac2):
    msg = json.dumps({"id": "invite", "mac": mac}, sort_keys=True, indent=4)
    msg2 = json.dumps({"id": "invite", "mac": mac2}, sort_keys=True, indent=4)

    result = client.publish(topic, msg)
    result = client.publish(topic, msg2)
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{topic}`")
        print(f"Send `{msg2}` to topic `{topic}`")
    else:
        print(f"Failed to send message to topic {topic}")


def run():
    index()


if __name__ == '__main__':
    # run()
    app.run(debug=True, host='127.0.0.1')
