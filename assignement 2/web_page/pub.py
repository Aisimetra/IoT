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
topic_data = "gmadotto1/data"
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
fire = 0
proximity = 0
rows = []


# HTML
@app.route('/')
def index():
    return render_template('home.html')


@app.route('/confirm', methods=['POST'])
def my_form_post():
    mac = request.form['slave'] # sopra
    mac2 = request.form['slave2'] # sotto
    mac_validation = bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})'] * 6) + '$', mac.lower()))

    if not mac_validation:
        return render_template('error.html', utc_dt="L'indirizzo MAC inserito è errato ")

    client = connect_mqtt()
    publish(client, mac, mac2)
    subscribe(client)
    client.loop_start()

    return render_template('confirm.html', title="stoccaggio", conf="lo stoccaggio")


@app.route('/new_node')
def index_page():
    return render_template('new_node.html')


@app.route('/home_con_Sensori')
def hom_sens():
    alarm_prod = my_sql_connection_select_high_production()
    alarm_storage = my_sql_connection_select_high_storage()
    storage = my_sql_connection_select_low()
    print('prossimità storage ' + alarm_storage[-2][2])
    print(alarm_storage)
    print(storage)
    print('temeratura' + storage[-1][1])
    print('percepita ' + storage[-1][2])
    print('umidità ' + storage[-1][3])
    # p incendio s intruso s incendio
    if alarm_prod[-3][1] == 'True' and alarm_storage[-2][2] == 'True' and alarm_storage[-2][1] == 'True':
        return render_template('home_con_Sensori.html', label1="Incendio", badge1="badge-danger", label2="Intruso",
                               badge2="badge-danger", label3="Incendio", badge3="badge-danger",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p tranquillo s intruso s incendio
    elif alarm_prod[-3][1] == 'False' and alarm_storage[-2][2] == 'True' and alarm_storage[-2][1] == 'True':
        return render_template('home_con_Sensori.html', label1="Tranquillo", badge1="badge-success", label2="Intruso",
                               badge2="badge-danger", label3="Incendio", badge3="badge-danger",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p incendio s intruso s tranquillo
    elif alarm_prod[-3][1] == 'True' and alarm_storage[-2][2] == 'True' and alarm_storage[-2][1] == 'False':
        return render_template('home_con_Sensori.html', label1="Incendio", badge1="badge-danger", label2="Intruso",
                               badge2="badge-danger", label3="Tranquillo", badge3="badge-success",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p tranquillo s no intruso s incendio
    elif alarm_prod[-3][1] == 'False' and alarm_storage[-2][2] == 'False' and alarm_storage[-2][1] == 'True':
        return render_template('home_con_Sensori.html', label1="Tranquillo", badge1="badge-success",
                               label2="Nessun Intruso", badge2="badge-success", label3="Incendio",
                               badge3="badge-danger",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p incendio s no intruso s tranquillo
    elif alarm_prod[-3][1] == 'True' and alarm_storage[-2][2] == 'False' and alarm_storage[-2][1] == 'False':
        return render_template('home_con_Sensori.html', label1="Incendio", badge1="badge-danger",
                               label2="Nessun Intruso", badge2="badge-success", label3="Tranquillo",
                               badge3="badge-success",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p tranquillo s intruso s tranquillo
    elif alarm_prod[-3][1] == 'False' and alarm_storage[-2][2] == 'True' and alarm_storage[-2][1] == 'False':
        return render_template('home_con_Sensori.html', label1="Tranquillo", badge1="badge-success", label2="Intruso",
                               badge2="badge-danger", label3="Tranquillo", badge3="badge-success",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p incendio s no intruso s incendio
    elif alarm_prod[-3][1] == 'True' and alarm_storage[-2][2] == 'False' and alarm_storage[-2][1] == 'True':
        return render_template('home_con_Sensori.html', label1="Incendio", badge1="badge-danger",
                               label2="Nessun Intruso", badge2="badge-success", label3="Incendio",
                               badge3="badge-danger",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])
    # p tranquillo s tranquillo s tranquillo
    else:
        return render_template('home_con_Sensori.html', label1="Tranquillo", badge1="badge-success",
                               label2="Nessun Intruso", badge2="badge-success", label3="Tranquillo",
                               badge3="badge-success",
                               temp_v=storage[-1][1], real_temp_v=storage[-1][2], hum_v=storage[-1][3])


def pd(last_dato):  # parsing divino
    string_parse = json.loads(last_dato)
    if string_parse['id'] == 'production' and string_parse['priority'] == 'low':
        temperature = str(string_parse['temperature'])
        real_temperature = str(string_parse['real_temperature'])
        humidity = str(string_parse['humidity'])
        print('production low')
        mysql_connection_insert_low(temperature, real_temperature, humidity)
    elif string_parse['id'] == 'production' and string_parse['priority'] == 'high':
        fire = str(string_parse['fire'])
        proximity = str(string_parse['proximity'])
        print('production high ')
        mysql_connection_insert_high('production', fire, proximity)
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high':
        fire = str(string_parse['fire'])
        proximity = str(string_parse['proximity'])
        print('priority high ')
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
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.production_low ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        return rows


@app.route("/", methods=['GET', 'POST'])
def my_sql_connection_select_high_production():
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.production_high ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        return rows


@app.route("/", methods=['GET', 'POST'])
def my_sql_connection_select_high_storage():
    with app.app_context():
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM asarteschi.storage_high ORDER BY id DESC LIMIT 1')
        for row in cursor:
            rows.append(row)
        mysql.connection.commit()
        cursor.close()
        return rows


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
