# python 3.6

import random
from paho.mqtt import client as mqtt_client
from flask import Flask, render_template, request
import re

# for flask
app = Flask(__name__)
# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'


# HTML
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/confirm', methods=['POST'])
def my_form_post():
    mac = request.form['slave']
    mac_validation = bool(re.match('^' + '[\:\-]'.join(['([0-9a-f]{2})'] * 6) + '$', mac.lower()))
    if not mac_validation:
        return render_template('error.html')
    client = connect_mqtt()
    publish(client, mac)
    return render_template('confirm.html')


@app.route('/sensor')
def sensor_page():
    return render_template('sensor.html')


# MQTT
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def publish(client, mac):
    msg = "{ \"id\":\"invite\", \"mac\":\"" + mac + "\"}"
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
