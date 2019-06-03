import json
import time
import schedule
import requests
import os
from datetime import datetime


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

def check_for_updates():
    global scheduled_msgs, filename, schedule 

    with open(filename, 'r') as f:
        file_content = json.load(f)
        if scheduled_msgs == file_content:  # return if no update
            return
        else:
            scheduled_msgs = file_content

    schedule.clear()

    # update one-time messages
    for msg in scheduled_msgs['Once']:
        schedule.every().day.at(msg['sched'][0]).do(send_msg, text=msg['text'], onetime=True).tag(msg['id'], 'Once')
        print('msg scheduled')

    # daily
    for msg in scheduled_msgs['Daily']:
        for sched in msg['sched']:
            schedule.every().day.at(sched).do(send_msg, text=msg['text']).tag(msg['id'], 'Daily')
    
    # monthly
    for msg in scheduled_msgs['Monthly']:
        for sched in msg['sched']:
            if datetime.now().day == sched[0]:
                schedule.every().day.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Monthly')
    
    # weekly
    for msg in scheduled_msgs['Weekly']:
        for sched in msg['sched']:
            if sched[0]==1:
                schedule.every().monday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')
            elif sched[0]==2:
                schedule.every().tuesday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')            
            elif sched[0]==3:
                schedule.every().wednesday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')
            elif sched[0]==4:
                schedule.every().thursday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')
            elif sched[0]==5:
                schedule.every().friday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')
            elif sched[0]==6:
                schedule.every().saturday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')
            elif sched[0]==7:
                schedule.every().sunday.at(sched[1]).do(send_msg, text=msg['text']).tag(msg['id'], 'Weekly')  
    
    print('File has been updated.')
    print('{} jobs running'.format(len(schedule.jobs)))
    return


# main program
while True:
    check_for_updates()
    schedule.run_pending()
    time.sleep(5)