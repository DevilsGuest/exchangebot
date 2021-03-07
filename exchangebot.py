# Exchangebot version 2.0.4
# Exchange bot developed by https://github.com/DevilsGuest/exchangebot
# Exchange Bot is a exchange rate informer!
# Terms and Conditions are discribed in LICENSE file
#
# Required Libreries
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, CallbackQueryHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, Message, Update
from configparser import ConfigParser
from requests import get
from json import dumps, loads
from math import ceil

# Config File

cfg = ConfigParser()

# Required Variables

admins = ('Your Chat ID',) # Chat ids of admins for restricted functions such as advertising
main_keyboard = ReplyKeyboardMarkup([
    ['About', 'Exchange Rate', 'Base Select']
])
currency_rates = get("https://api.exchangeratesapi.io/latest").json()['rates']
rates = []
for rate in currency_rates:
    rates.append(InlineKeyboardButton(rate, callback_data=rate))
rates = [
    rates[i * 4:(i * 4) + 4]
    for i in range(ceil(len(rates) / 4))
]
currency_base_keyboard = InlineKeyboardMarkup(rates)
config_file = open('config.cfg', 'r')
api_token = config_file.readlines()[1][10:]
config_file.close()
updater = Updater(api_token) # Put your token in the config.cfg file
handler = updater.dispatcher.add_handler
chat_id_list = dict()
REPLY = 0
with open('userlist/chat_id_list.json', 'r') as dic:
    chat_id_list = loads(dic.read())
    dic.close()

# Functions

def start(update : Update, context : CallbackContext):
    """ Function to start the bot and show initial information """
    send_message = update.message.reply_text
    send_message("Started Exchange Bot...\nWelcome {}!\nExchange Bot is a exchange rate informer.".format(update.message.from_user.first_name), reply_markup=main_keyboard)
    cfg['USER_CFG'] = {'BASE_CURRENCY' : 'USD'}
    with open('sessions/' + str(update.message.chat_id) + '.cfg', 'w') as user_cfg:
        cfg.write(user_cfg)
        user_cfg.close()
    with open('userlist/chat_id_list.json', 'w') as ids:
        chat_id_list[str(update.message.chat_id)] = update.message.from_user.username
        ids.write(dumps(chat_id_list))
        ids.close()

def about(update : Update, context : CallbackContext):
    """ Shows information about the bot """
    send_message = update.message.reply_text
    send_message("Exchange Bot is a exchange rate informer!\nDeveloped by https://github.com/DevilsGuest")

def get_rates_query(update : Update, context : CallbackContext):
    """Get exchange rate info from API\n
        Called by CallbackQueryHandler
    """
    query = update.callback_query
    send_message = query.message.reply_text
    send_message('Getting data from server...')
    cfg.read('sessions/' + str(query.message.chat_id) + '.cfg')
    readconfig = cfg['USER_CFG']
    response = get("https://api.exchangeratesapi.io/latest?base={}".format(readconfig['BASE_CURRENCY'])).json()
    rates = ""
    for rate in response['rates']:
        if rate != readconfig['BASE_CURRENCY']:
            rates += str(rate) + ' : ' + str(response['rates'][rate]) + "\n"
    send_message('Date : ' + str(response['date']) + "\n" + 'Base : ' + readconfig['BASE_CURRENCY'] + "\n" + rates)

def get_rates(update : Update, context : CallbackContext):
    """ Get exchange rate info from API """
    send_message = update.message.reply_text
    send_message('Getting data from server...')
    cfg.read('sessions/' + str(update.message.chat_id) + '.cfg')
    readconfig = cfg['USER_CFG']
    response = get("https://api.exchangeratesapi.io/latest?base={}".format(readconfig['BASE_CURRENCY'])).json()
    rates = ""
    for rate in response['rates']:
        if rate != readconfig['BASE_CURRENCY']:
            rates += str(rate) + ' : ' + str(response['rates'][rate]) + "\n"
    send_message('Date : ' + str(response['date']) + "\n" + 'Base : ' + readconfig['BASE_CURRENCY'] + "\n" + rates)

def base_select(update : Update, context : CallbackContext):
    """ Calls on get_rates_query based on callback data of currency_base_keyboard """
    query = update.callback_query
    send_message = query.message.reply_text
    answer = query.answer
    edit_message = query.edit_message_text
    edited_keyboard = [
        [InlineKeyboardButton('Show Rates', callback_data='show_rates')]
    ]
    edited_keyboard = InlineKeyboardMarkup(edited_keyboard)
    response = get('https://api.exchangeratesapi.io/latest?base=USD').json()
    if query.data in list(response['rates'].keys()):
        cfg.read('sessions/' + str(query.message.chat_id) + '.cfg')
        cfg.set('USER_CFG', 'BASE_CURRENCY', query.data)
        with open('sessions/' + str(query.message.chat_id) + '.cfg', 'w') as conf:
            cfg.write(conf)
            conf.close()
        answer('Base currency set successfuly!')
        edit_message('Do you want to show rates now? click on Show Rates', reply_markup=edited_keyboard)
    elif query.data in ['show_rates']:
        get_rates_query(update, context)
    else:
        send_message('Base currency set Failed!')

def message_handler(update : Update, context : CallbackContext):
    """ Handles none command messages """
    send_message = update.message.reply_text
    text = str(update.message.text).lower()
    if text in ['info', 'about', 'discrinption']:
        # Discription and info about Exchange Bot
        about(update, context)
    elif text in ['exchange rate', 'exchangerate']:
        # Get exchange rate info from API
        get_rates(update, context)
    elif text in ['base select', 'baseselect']:
        # Show base select inline keyboard
        send_message('Choose a base Currency :', reply_markup=currency_base_keyboard)
    else:
        # Not recognized commands
        send_message("Command or message was not recognized!\nNote that some commands or messages might be case sensetive.")

# Admin Functions

# Begin Advertise conversation
def advertise(update : Update, context : CallbackContext):
    """ Waits for a message to be forwarded to users in userlist\n
        Called by ConversationHandler\n
            returns REPLY
    """
    ad_keyboard = ReplyKeyboardMarkup([['Cancel']])
    send_message = update.message.reply_text
    if update.message.chat_id in admins:
        send_message('Users : ' + str(len(chat_id_list)))
        send_message('Send a message to be advertised...', reply_markup=ad_keyboard)
        return REPLY
    else:
        return ConversationHandler.END

def send_ad(update : Update, context : CallbackContext):
    """ Forwards the message recieved by advertise() to users """
    send_message = update.message.reply_text
    success = True
    for user in chat_id_list:
        try:
            update.message.forward(user)
        except :
            success = False
    if success:
        send_message('Message advertised successfuly!', reply_markup=main_keyboard)
    else:
        send_message('Message advertising Failed!', reply_markup=main_keyboard)
    return ConversationHandler.END

def cancel(update : Update, context : CallbackContext):
    """ Cancels current conversation """
    send_message = update.message.reply_text
    send_message('Process Stoped!', reply_markup=main_keyboard)
    return ConversationHandler.END
# End Advertise conversation

# Handlers
handler(CommandHandler('start', start))
handler(CommandHandler('about', about))
handler(CommandHandler('exchangerate', get_rates))
handler(CallbackQueryHandler(base_select))
handler(ConversationHandler(
    entry_points=[CommandHandler('ad', advertise)],
    states= {
        REPLY: [MessageHandler(Filters.all & ~Filters.text(['Cancel', 'cancel']), send_ad)]
    },
    fallbacks=[MessageHandler(Filters.text(['Cancel', 'cancel']), cancel)]
))
handler(MessageHandler(Filters.text, message_handler))

# Starts recieving messages
updater.start_polling()

# Blocks incomig texts until a message is recieved by Updater
updater.idle()

print("Exchange Bot is running...\nDeveloped by https://github.com/DevilsGuest")