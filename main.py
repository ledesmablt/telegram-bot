import json
import logging
from uuid import uuid1
from dateutil import parser
from itertools import product

from telegram.utils.helpers import escape_markdown

from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

# add telegram bot parameters
secret_path = 'data/secret.json'
with open(secret_path, 'r') as f:
    secret_info = json.load(f)

tg_token = secret_info['TOKEN']
chat_id = secret_info['CHAT_ID']

# enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)


filename = 'data/scheduled_msgs.json'
msg_info = {    # notif_message, 'Monthly/Weekly/Daily', mo/week sched (None if Daily), times (hr, min)
    'text':None,
    'setting':None,
    'mw_sched':None,
    'time_sched':None
}


try:
    with open(filename, 'r') as f:
        all_scheduled_msgs = json.load(f)
except:
    all_scheduled_msgs = {
        'Weekly':[],    # {id, text, [day, time]}
        'Monthly':[],   # {id, text, [day, time]}
        'Daily':[],     # {id, text, time}
        'Once':[]       # {id, text, time}
    }

output = {
    'setting':None,
    'content':None
}

def reset_variables():
    global output, msg_info
    output = {'setting':None, 'content':None}
    msg_info = {'text':None, 'setting':None, 'mw_sched':None, 'time_sched':None}


def create_msg(bot, update):
    update.message.reply_text(
        "Please input the message you want to receive."
    )
    return 'MSG'

def schedule_msg(bot, update):
    reply_keyboard = [['Monthly', 'Weekly', 'Daily', 'Once']]
    res = update.message.text
    msg_info['text'] = res

    update.message.reply_text(
        "I want this to run...",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    )

    return 'SCHEDULE'

def schedule_any(bot, update):
    res = update.message.text
    msg_info['setting'] = res

    if res == 'Monthly':
        update.message.reply_text(
            "Please enter the day/s (1-30) when you want to receive the message, separated by spaces.",
            reply_markup=ReplyKeyboardRemove()
        )
        return 'TIME'

    elif res == 'Weekly':
        update.message.reply_text(
            """Please select the day/s when you want to receive the message, separated by spaces.\n
            1 - 7 : Monday - Sunday""",
            reply_markup=ReplyKeyboardRemove()
        )
        return 'TIME'
    
    else:
        return ConversationHandler.END

def schedule_time(bot, update):
    res = update.message.text

    if msg_info['setting'] in ('Monthly','Weekly'):
        mo_days = [int(i) for i in res.split(' ')]
        msg_info['mw_sched'] = mo_days
    
    else:   # is either daily or once
        msg_info['setting'] = res

    update.message.reply_text(
        """Please enter what time/s you would like to receive the message, separated by spaces.\n
        ex. 1:30PM"""
    )

    return 'CONFIRM'
    
def confirm(bot, update):
    res = update.message.text
    complete_sched = []
    reply_keyboard = [['Yes', 'No']]

    time_sched = ['{}:{}'.format(parser.parse(i).strftime('%H:%M')) for i in res.split(' ')]
    msg_info['time_sched'] = time_sched

    if msg_info['setting'] in ('Daily', 'Once'):
        complete_sched = time_sched
    else:
        # [day (of month/week), time]
        complete_sched = [[i[0], i[1]] for i in product(msg_info['mw_sched'], msg_info['time_sched'])]

    output['setting'] = msg_info['setting']
    output['content'] = {
        'id' : str(uuid1().int),
        'text' : msg_info['text'],
        'sched' : complete_sched
    }

    update.message.reply_text(
        """Confirm these settings?\n\n
            {0}\n\n{1}
            """.format(complete_sched, msg_info['text']),
            reply_markup=ReplyKeyboardMarkup(reply_keyboard)
    )

    return 'SAVE'

def save(bot, update):
    global output, msg_info
    res = update.message.text
    if res == 'Yes':
        all_scheduled_msgs[output['setting']].append(output['content'])
        with open(filename, 'w') as f:
            json.dump(all_scheduled_msgs, f)
            logger.info('Results written to file.')

        update.message.reply_text(
            "Your settings have been saved.",
            reply_markup=ReplyKeyboardRemove()
        )
    elif res == 'No':
        update.message.reply_text(
            "!!! Your settings have been discareded.",
            reply_markup=ReplyKeyboardRemove()
        )

    # reset variables
    reset_variables()

    return ConversationHandler.END


### from test.py
def cancel(bot, update):
    reset_variables()
    logger.info("User canceled the conversation.")
    update.message.reply_text(
        'User canceled the conversation.',
        reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


# main program

updater = Updater(tg_token)
dp = updater.dispatcher

sched_handler = ConversationHandler(
    entry_points=[
        CommandHandler('schedule', create_msg)
    ],

    states={
        'MSG': [MessageHandler(Filters.text, schedule_msg)],
        'SCHEDULE': [
            RegexHandler('^(Monthly|Weekly)$', schedule_any),
            RegexHandler('^(Daily|Once)$', schedule_time)
        ],
        'TIME' : [MessageHandler(Filters.text, schedule_time)],
        'CONFIRM' : [MessageHandler(Filters.text, confirm)],
        'SAVE' : [MessageHandler(Filters.text, save)]
    },

    fallbacks=[CommandHandler('cancel', cancel)]

)

dp.add_handler(sched_handler)
dp.add_error_handler(error)
updater.start_polling()
updater.idle()