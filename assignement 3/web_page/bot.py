#!/usr/bin/env python
# pylint: disable=C0116
# This program is dedicated to the public domain under the CC0 license.

"""
First, a few callback functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Example of a bot-user conversation using ConversationHandler.
Send /start to initiate the conversation.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
from typing import Dict

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

from pub import my_sql_connection_select_low

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
    update.message.reply_text(f'Prossimità')

    return CHOOSING


def temp(update: Update, _: CallbackContext) -> int:
    storage = my_sql_connection_select_low()

    update.message.reply_text(
        'La temperatura in questo momento nello stoccaggio è di  ' + storage[2]
    )

    return CHOOSING


def hum(update: Update, _: CallbackContext) -> int:
    storage = my_sql_connection_select_low()

    update.message.reply_text(
        'L\'umidità in questo momento nello stoccaggio è di  ' + storage[4]
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


if __name__ == '__main__':
    main()







---------------

import os
import time

import paho.mqtt.client as mqtt

from telegram.bot import Bot
from telegram.parsemode import ParseMode

# initializing the bot with API_KEY and CHAT_ID
if os.getenv('TELEGRAM_BOT_API_KEY') == None:
    print("Error: Please set the environment variable TELEGRAM_BOT_API_KEY and try again.")
    exit(1)
bot = Bot(os.getenv('TELEGRAM_BOT_API_KEY'))

if os.getenv('TELEGRAM_BOT_CHAT_ID') == None:
    print("Error: Please set the environment variable TELEGRAM_BOT_CHAT_ID and try again.")
    exit(1)
chat_id = os.getenv('TELEGRAM_BOT_CHAT_ID')

# based on example from https://pypi.org/project/paho-mqtt/
# The callback for when the client receives a CONNACK response from the server.


def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    if rc == 0:
        print("Connected successfully to broker")
    else:
        print("Connection failed")

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.

    # client.subscribe("teslamate/cars/1/version")
    client.subscribe("teslamate/cars/1/update_available")


# The callback for when a PUBLISH message is received from the server.


def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload.decode()))

    if msg.payload.decode() == "true":
        print("A new SW update for your Tesla is available!")
        bot.send_message(
            chat_id,
            # text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!\n\n<b>"+msg.topic+"</b>\n"+str(msg.payload.decode()),
            text="<b>"+"SW Update"+"</b>\n"+"A new SW update for your Tesla is available!",
            parse_mode=ParseMode.HTML,
        )


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.username_pw_set
if os.getenv('MQTT_BROKER_USERNAME') == None:
    pass
else:
    if os.getenv('MQTT_BROKER_PASSWORD') == None:
        client.username_pw_set(os.getenv('MQTT_BROKER_USERNAME', ''))
    else:
        client.username_pw_set(os.getenv('MQTT_BROKER_USERNAME', ''), os.getenv('MQTT_BROKER_PASSWORD', ''))

client.connect(os.getenv('MQTT_BROKER_HOST', '127.0.0.1'),
               int(os.getenv('MQTT_BROKER_PORT', 1883)), 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
# client.loop_forever()


client.loop_start()  # start the loop
try:

    while True:

        time.sleep(1)

except KeyboardInterrupt:

    print("exiting")


client.disconnect()

client.loop_stop()
