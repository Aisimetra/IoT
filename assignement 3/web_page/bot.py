import logging
import random
from typing import Dict
import emoji
import requests

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
    mysql_connection_insert_high, check_db_table, api_meteo

# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
topic_data = "gmadotto1/data"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'

#


# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

reply_keyboard = [
    ['Previsioni del tempo'],
    ['Temperatura nello Stoccaggio'],
    ['Umidità nello Stoccaggio'],
    ['Gabriele'],
    ['Termina']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)


def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, _: CallbackContext) -> int:
    update.message.reply_text(
        'Da questo momento riceverai tutti gli allarmi della vigna'
        'Puoi chiedermi tramite la tastiera: '
        '\n\n- di conoscere la temperatura nello stoccaggio'
        '\n\n- di conoscere l\'umidità nello stoccaggio'
        '\n\nInviami /cancel per smettere di parlarmi.\n\n',
        reply_markup=markup,
    )

    return CHOOSING


def temp(update: Update, _: CallbackContext) -> int:
    storage = my_sql_connection_select_low()
    update.message.reply_text(
        'La temperatura in questo momento nello stoccaggio è ' + storage[2] + '°C'
    )

    return CHOOSING


def prev(update: Update, _: CallbackContext) -> int:
    CITY, temperature, cloud, wind, iconUrl, iconCode = api_meteo()
    icon = map_icon(iconCode)
    update.message.reply_text(
        'La temperatura a ' + str(CITY) + 'è di ' + str(temperature) + '°C'
                                                                       '\nLa velocità del vento è di ' + str(
            wind) + ' m/s'
                    '\n La situazione nuvole è ' + str(cloud) + ' ' + icon
    )

    return CHOOSING


def map_icon(iconUrl):
    if iconUrl == '01d':
        return emoji.emojize(':sunny:', language='alias')
    elif iconUrl == '01n':
        return emoji.emojize(':full_moon:', language='alias')
    elif iconUrl == '02d':
        return emoji.emojize(':partly_sunny:', language='alias')
    elif iconUrl == '02n':
        return emoji.emojize(':partly_sunny:', language='alias')
    elif iconUrl == '03d':
        return emoji.emojize(':cloud:', language='alias')
    elif iconUrl == '03n':
        return emoji.emojize(':cloud:', language='alias')
    elif iconUrl == '04d':
        return emoji.emojize(':cloud:', language='alias')
    elif iconUrl == '04n':
        return emoji.emojize(':cloud:', language='alias')
    elif iconUrl == '09d':
        return emoji.emojize(':cloud_with_rain:', language='alias')
    elif iconUrl == '09n':
        return emoji.emojize(':cloud_with_rain:', language='alias')
    elif iconUrl == '10d':
        return emoji.emojize(':cloud_with_rain:', language='alias')
    elif iconUrl == '10n':
        return emoji.emojize(':cloud_with_rain:', language='alias')
    elif iconUrl == '11d':
        return emoji.emojize(':thunder_cloud_and_rain:', language='alias')
    elif iconUrl == '11n':
        return emoji.emojize(':thunder_cloud_and_rain:', language='alias')
    elif iconUrl == '13d':
        return emoji.emojize(':snow:', language='alias')
    elif iconUrl == '13n':
        return emoji.emojize(':snow:', language='alias')
    elif iconUrl == '50d':
        return emoji.emojize(':fog:', language='alias')
    elif iconUrl == '50n':
        return emoji.emojize(':fog:', language='alias')


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

    updater = Updater("5514482549:AAHiP3MoIlocnSZUmbpKxx0GW2f6nxy2deQ")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    # client = connect_mqtt()
    # subscribe(client)
    # client.loop_start()
    # Add conversation handler with the states CHOOSING, TYPING_CHOICE and TYPING_REPLY
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^(Previsioni del tempo)$'), prev),
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
