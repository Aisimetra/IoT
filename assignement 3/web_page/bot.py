import logging

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    ConversationHandler,
    CallbackContext,
)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

logger = logging.getLogger(__name__)

ALARM, TEMP_HUM, PIOVE, VENTO = range(4)


def start(update: Update, _: CallbackContext) -> int:
    reply_keyboard = [['Invia notifica di Allarme'], ['Temperatura e Umidità nello Stoccaggio'], ['Piove'], ['Vento']]

    update.message.reply_text(
        'Ciao! Io sono il bot che ti permetterà di monitorare i parametri del tuo vigneto! ',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False),
    )

    update.message.reply_text(
        'Puoi chiedermi tramite la tastiera: '
        '\n\n- di mandarti messaggi di allarme per intrusione'
        '\n\n- di conoscere la temperatura/ umidità nello stoccaggio'
        '\n\n- la probabilità di pioggia/ se piove'
        '\n\n- la velocità del vento'
        '\n\nInviami /cancel per smettere di parlarmi.\n\n',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True),
    )

    return ALARM


# settaggio degli allarmi
def alarm(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("Gender of %s: %s", user.first_name, update.message.text)
    update.message.reply_text(
        'I see! Please send me a temp_hum of yourself, '
        'so I know what you look like, or send /skip if you don\'t want to.',
        reply_markup=ReplyKeyboardRemove(),
    )

    return TEMP_HUM  # DOVE DEVE ANDARE DOPO


def temp_hum(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    temp_hum_file = update.message.temp_hum[-1].get_file()
    temp_hum_file.download('user_temp_hum.jpg')
    logger.info("temp_hum of %s: %s", user.first_name, 'user_temp_hum.jpg')
    update.message.reply_text(
        'Gorgeous! Now, send me your piove please, or send /skip if you don\'t want to.'
    )

    return PIOVE


def skip_temp_hum(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a temp_hum.", user.first_name)
    update.message.reply_text(
        'I bet you look great! Now, send me your piove please, or send /skip.'
    )

    return PIOVE


def piove(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    user_piove = update.message.piove
    logger.info(
        "piove of %s: %f / %f", user.first_name, user_piove.latitude, user_piove.longitude
    )
    update.message.reply_text(
        'Maybe I can visit you sometime! At last, tell me something about yourself.'
    )

    return VENTO


def skip_piove(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s did not send a piove.", user.first_name)
    update.message.reply_text(
        'You seem a bit paranoid! At last, tell me something about yourself.'
    )

    return VENTO


def vento(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("vento of %s: %s", user.first_name, update.message.text)
    update.message.reply_text('Thank you! I hope we can talk again some day.')

    return ConversationHandler.END


def cancel(update: Update, _: CallbackContext) -> int:
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    update.message.reply_text(
        'Bye! I hope we can talk again some day.', reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    # Create the Updater and pass it your bot's token.
    updater = Updater("5537150617:AAE8ifKEb3ZoeOuiUBSAOL2_Y0IyORXkFbc")

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Add conversation handler with the states GENDER, temp_hum, piove and vento -> stati finiti
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            ALARM: [MessageHandler(Filters.regex('^(Boy|Girl|Other)$'), alarm)],
            temp_hum: [MessageHandler(Filters.text, temp_hum), CommandHandler('skip', skip_temp_hum)],
            piove: [
                MessageHandler(Filters.text, piove),
                CommandHandler('skip', skip_piove),
            ],
            vento: [MessageHandler(Filters.text & ~Filters.command, vento)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],

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
