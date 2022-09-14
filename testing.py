import datetime
import lingua_franca
from lingua_franca import parse, format
lingua_franca.load_language('en')
import pickle
import os
import re
import pytz

#working code
from datetime import datetime


# make plural wait_h-1 hours
def curent_time_extraction():
    now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%H:%M %p")
    day_time = now.lower().split(' ')
    print(day_time)
    exact_time = day_time[0].split(':')
    hour, min = int(exact_time[0]), int(exact_time[1])
    return hour, min

shop_name = 'Apple'

def time_calculation(time, shop_name):
    hour, min = curent_time_extraction()
    hour, min = int(8), int(59)
    day_time = ['time', 'am']
    time = '9am - 8pm'

    parse_time = time.split('-')
    open_time = int(re.sub('[^\d+]', '',parse_time[0]))
    close_time = int(re.sub('[^\d+]', '',parse_time[1]))
    print(int(open_time))
    print(int(close_time))
    if day_time[1]=='am' and hour<open_time:
        time_before_opening_closing(open_time, hour, min, 'opens', shop_name)
    elif day_time[1]=='pm' and hour<close_time:
        time_before_opening_closing(close_time, hour, min, 'opens', shop_name)
    else:
        print(f'{shop_name} is open now.')
    
def time_before_opening_closing(work_time, hour, min, word, shop_name):
        wait_h = work_time-hour-1
        wait_min = 60-min
        if wait_h == 1:
            print(f'{shop_name} is closed now. Shop {word} in {wait_h} hour and {wait_min} minutes')
        elif wait_h != 0:
            print(f'{shop_name} is closed now. Shop {word} in {wait_h} hours and {wait_min} minutes')
        else:
            if wait_min ==1:
                print(f'{shop_name} is closed now. Shop {word} in {wait_min} minute')
            else:
                print(f'{shop_name} is closed now. Shop {word} in {wait_min} minutes')



