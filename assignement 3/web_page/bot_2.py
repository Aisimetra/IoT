import logging
import random
from typing import Dict
import requests

import telegram_send
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)
from paho.mqtt import client as mqtt_client
import json

from pub import my_sql_connection_select_low, mysql_connection_insert_low, \
    mysql_connection_insert_high, check_db_table

# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
topic_data = "gmadotto1/data"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Alarmi'],
    ['Temperatura nello Stoccaggio'],
    ['Umidità nello Stoccaggio'],
    ['Gabriele'],
    ['Termina']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Puoi chiedermi tramite la tastiera: '
        '\n\n- di mandarti messaggi di allarme per intrusione'
        '\n\n- di conoscere la temperatura/ umidità nello stoccaggio'
        '\n\n- la probabilità di pioggia/ se piove'
        '\n\n- la velocità del vento'
        '\n\nInviami /cancel per smettere di parlarmi.\n\n',
        reply_markup=markup,
    )

    return CHOOSING


def alarm(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Attivo la ricezione degli alarmi')

    return CHOOSING


def alarm_proximity(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Intrusione nello stoccaggio')
    print('entra in prossimità')

    return CHOOSING


def alarm_fire(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Incendio nella produzione')
    print('entra in produzione incendio')

    return CHOOSING


def alarm_fire_stoc(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(f'Incendio nello stoccaggio')
    print('entra in stoccaggio incendio')

    return CHOOSING


def temp(update: Update, _: CallbackContext) -> int:
    storage = my_sql_connection_select_low()
    update.message.reply_text(
        'La temperatura in questo momento nello stoccaggio  è ' + storage[2] + '°C'
    )

    return CHOOSING


def hum(update: Update, _: CallbackContext) -> int:
    storage = my_sql_connection_select_low()
    update.message.reply_text(
        'L\'umidità in questo momento nello stoccaggio è del ' + storage[4] + '%'
    )

    return CHOOSING


def pera(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        '\U0001F350'
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"Grazie per aver utilizzato il nostro bot!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.

    updater = Updater("5423079267:AAGp166tckTwLGsL3TwF7dXPg9n6m6Gm9AA")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    client = connect_mqtt()
    subscribe(client)
    client.loop_start()
    print("polo")
    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^(Alarmi)$'), alarm),
                MessageHandler(Filters.regex('^(Temperatura nello Stoccaggio)$'), temp),
                MessageHandler(Filters.regex('^(Umidità nello Stoccaggio)$'), hum),
                MessageHandler(Filters.regex('^(Gabriele)$'), pera),
                MessageHandler(Filters.regex('^(Termina)$'), done)
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


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


messages = []


def subscribe(client: mqtt_client):
    print("polo0")

    def on_message(client, userdata, msg):
        print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        messages.append(str(msg.payload.decode("utf-8")))
        conf = json.loads(messages[-1])
        print(messages[-1])
        pd(messages[-1])

    client.subscribe(topic)
    client.subscribe(topic_data)
    client.on_message = on_message


def pd(last_dato):  # parsing divino
    string_parse = json.loads(last_dato)

    check_db_table('asarteschi.production_low')
    check_db_table('asarteschi.production_high')
    check_db_table('asarteschi.storage_high')

    if string_parse['id'] == 'production' and string_parse['priority'] == 'high':
        alarm_fire()
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high' and string_parse['fire'] == 'true' and \
            string_parse['proximity'] == 'true':
        alarm_fire_stoc()
        alarm_proximity()
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high' and string_parse['fire'] == 'true':
        alarm_fire_stoc()
    elif string_parse['id'] == 'storage' and string_parse['priority'] == 'high' and string_parse['proximity'] == 'true':
        alarm_proximity()
    else:
        print('Si è rotto ')


if __name__ == '__main__':
    main()
