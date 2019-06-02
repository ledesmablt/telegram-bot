import json
import time
import schedule
import requests


# add telegram bot parameters
secret_path = 'data/secret.json'
with open(secret_path, 'r') as f:
    secret_info = json.load(f)

tg_token = secret_info['TOKEN']
chat_id = secret_info['CHAT_ID']
tg_api = 'https://api.telegram.org/bot{}/sendMessage?chat_id={}&parse_mode=Markdown&text={}'

scheduled_msgs = None
filename = 'data/scheduled_msgs.json'

def send_msg(text, onetime=False):
    requests.get(tg_api.format(tg_token, chat_id, text))
    return schedule.CancelJob if onetime else None

def check_for_updates(scheduled_msgs, filename, schedule):
    with open(filename, 'r') as f:
        file_content = json.load(f)
        if scheduled_msgs == file_content:  # return if no update
            return
        else:
            scheduled_msgs = file_content

    # update one-time messages
    for msg in scheduled_msgs['Once']:
        schedule.every().day.at(msg['sched'][0]).do(send_msg, text=msg['text'], onetime=True)
        print('msg scheduled')
    
    print('File has been updated.')
    return


# main program
while True:
    check_for_updates(scheduled_msgs, filename, schedule)
    schedule.run_pending()
    time.sleep(30)