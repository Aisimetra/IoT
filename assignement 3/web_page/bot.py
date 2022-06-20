import asyncio
import logging
import random
from time import sleep, strftime
from typing import Dict
import emoji
from flask import Flask
from flask_mysqldb import MySQL
from telegram import ReplyKeyboardMarkup, Update, ReplyKeyboardRemove
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

from pub import api_meteo

# for mqtt
broker = '149.132.178.180'
port = 1883
topic = "gmadotto1/general"
topic_data = "gmadotto1/data"
client_id = f'python-mqtt-{random.randint(0, 1000)}'
username = 'asarteschi'
password = 'iot829677'

chat_ids = []

app = Flask(__name__)
app.config['MYSQL_HOST'] = '149.132.178.180'
app.config['MYSQL_USER'] = 'asarteschi'
app.config['MYSQL_PASSWORD'] = 'iot829677'
app.config['MYSQL_DB'] = 'asarteschi'
app.config['MYSQL_DATABASE_PORT'] = 3306
mysql = MySQL(app)

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
    ['Termina']
]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)


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


def facts_to_str(user_data: Dict[str, str]) -> str:
    facts = list()

    for key, value in user_data.items():
        facts.append(f'{key} - {value}')

    return "\n".join(facts).join(['\n', '\n'])


def start(update: Update, context: CallbackContext) -> int:
    update.message.reply_text(
        'Da questo momento riceverai tutti gli allarmi della vigna'
        'Puoi chiedermi tramite la tastiera: '
        '\n\n- di conoscere le previsioni del tempo alla vigna'
        '\n\n- di conoscere la temperatura nello stoccaggio'
        '\n\n- di conoscere l\'umidità nello stoccaggio'
        '\n\nOppure terminare il bot\n\n',
        reply_markup=markup,
    )
    id_to_store = update.effective_chat.id
    print(id_to_store)
    #user id, prod_prev_timestamp, storage_prev_timestamp
    if not chat_ids:
        user_log = (id_to_store, "", "")
        chat_ids.append(user_log)
    elif id_to_store not in chat_ids:
        user_log = (id_to_store, "", "")
        chat_ids.append(user_log)
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
                    '\nLa situazione nuvole è ' + str(cloud) + ' ' + icon
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

def arte(update: Update, _: CallbackContext) -> int:
    update.message.reply_photo(photo=open('artemisia.jpg', 'rb'))

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    for i in range(0, len(chat_ids)):
        if chat_ids[i][0] == update.effective_chat.id:
            chat_ids.remove(chat_ids[i])
            break
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"Grazie per aver utilizzato il nostro bot!",
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END


def send_alarm_notification(bot):
    #prev_storage_timestamp = ""
    #prev_production_timestamp = ""
    while True:
        storage_alarm = my_sql_connection_select_high_storage()
        production_alarm = my_sql_connection_select_high_production()
        cur_timestamp_stor = storage_alarm[1].strftime('%Y-%m-%d %H:%M:%S')
        cur_timestamp_prod = production_alarm[1].strftime('%Y-%m-%d %H:%M:%S')
        print(chat_ids)
        for i in range(0, len(chat_ids)):
        #for chat_id in chat_ids:
            if not cur_timestamp_prod == chat_ids[i][1]:
                if production_alarm[2] == 'True' or production_alarm[2] == 'true':
                    msg = 'ALLARME IN PRODUZIONE: INCENDIO\n'
                    #production_alarm[1][3] += production_alarm[1][3] + 2
                    msg += 'Orario di rilevamento: ' + production_alarm[1].strftime('%Y-%m-%d %H:%M:%S')
                    bot.send_message(text=msg, chat_id=chat_ids[i][0])
                    # chat_ids[i][1] = cur_timestamp_prod
                    new_val = (chat_ids[i][0], cur_timestamp_prod, chat_ids[i][2])
                    chat_ids[i] = new_val

            if not cur_timestamp_stor == chat_ids[i][2]:
                if storage_alarm[2] == 'True' or storage_alarm[2] == 'true':
                    msg = 'ALLARME IN STOCCAGGIO: INCENDIO\n'
                    #storage_alarm[1][3] += storage_alarm[1][3] + 2
                    msg += 'Orario di rilevamento: ' + storage_alarm[1].strftime('%Y-%m-%d %H:%M:%S')
                    bot.send_message(text=msg, chat_id=chat_ids[i][0])
                    # chat_ids[i][2] = cur_timestamp_stor
                    new_val = (chat_ids[i][0], chat_ids[i][1], cur_timestamp_stor)
                    chat_ids[i] = new_val

                if storage_alarm[3] == 'True' or storage_alarm[3] == 'true':
                    msg = 'ALLARME IN STOCCAGGIO: INTRUSO\n'
                    #storage_alarm[1][3] += production_alarm[1][3] + 2
                    msg += 'Orario di rilevamento: ' + storage_alarm[1].strftime('%Y-%m-%d %H:%M:%S')
                    bot.send_message(text=msg, chat_id=chat_ids[i][0])
                    new_val = (chat_ids[i][0], chat_ids[i][1], cur_timestamp_stor)
                    chat_ids[i] = new_val

            # bot.send_message(text='studia artemisia', chat_id=chat_id)
        #if not chat_ids == []:
            #prev_production_timestamp = cur_timestamp_prod
            #prev_storage_timestamp = cur_timestamp_stor
        sleep(3)


def main() -> None:
    # Create the Updater and pass it your bot's token.

    updater = Updater("5514482549:AAHiP3MoIlocnSZUmbpKxx0GW2f6nxy2deQ", use_context=True)

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.run_async(send_alarm_notification, updater.bot)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [
                MessageHandler(Filters.regex('^(Previsioni del tempo)$'), prev),
                MessageHandler(Filters.regex('^(Temperatura nello Stoccaggio)$'), temp),
                MessageHandler(Filters.regex('^(Umidità nello Stoccaggio)$'), hum),
                MessageHandler(Filters.regex('^(Termina)$'), done),
                # MessageHandler(Filters.regex('None'), send_alarm_notification)
            ]
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
