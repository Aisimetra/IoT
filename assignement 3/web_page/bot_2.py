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
    update.message.reply_text(f'Se Aisimetra lo imposta potrai-> Attivare gli allarmi!')

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


def received_information(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    text = update.message.text
    category = user_data['choice']
    user_data[category] = text
    del user_data['choice']

    update.message.reply_text(
        "Neat! Just so you know, this is what you already told me:"
        f"{facts_to_str(user_data)} You can tell me more, or change your opinion"
        " on something.",
        reply_markup=markup,
    )

    return CHOOSING


def done(update: Update, context: CallbackContext) -> int:
    user_data = context.user_data
    if 'choice' in user_data:
        del user_data['choice']

    update.message.reply_text(
        f"I learned these facts about you: {facts_to_str(user_data)}Until next time!",
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
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')), alarm
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    Filters.text & ~(Filters.command | Filters.regex('^Done$')),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(Filters.regex('^Done$'), done)],
    )

    dispatcher.add_handler(conv_handler)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
