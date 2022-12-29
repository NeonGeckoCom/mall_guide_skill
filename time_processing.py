# time operations
from datetime import datetime
from neon_utils.skills.neon_skill import LOG
import re

def change_format(time):
    """
    Changing format from 12h to 24h.
    Returns:
        formated_time (list): [int(hour), int(min)]
    """
    in_time = datetime.strptime(time, "%I:%M %p")
    out_time = datetime.strftime(in_time, "%H:%M")
    hour_min = out_time.split(':')
    formated_time = [int(hour_min[0]), int(hour_min[1])]
    return formated_time

def time_refactoring(time_str):
    """
    Adding space detween time and am|pm.
    If working time doesn't have mins add them.
    Args:
        time_str (list): store's work time
    Returns:
        open_time (list): open_h (int), open_m (int),
        close_time (list): close_h (int), close_m (int),
    """
    if ':' not in time_str:
        time_refactored = re.sub(r'(\d+)(am|pm)', '\g<1>:00 \g<2>', time_str)
    else:
        time_refactored = re.sub(r'(am|pm)', ' \g<1>', time_str)
    new_format = change_format(time_refactored)
    return new_format

def left_lime_calculation(user_h, user_m, work_h, work_m):
    if work_m < user_m:
        wait_min = user_m - work_m
    else:
        wait_min = work_m - user_m
    wait_h_opening = work_h - user_h
    LOG.info(f'Hour difference {wait_h_opening}')
    duration = wait_h_opening * 3600 + wait_min * 60
    return duration

def open_stores_search(store_info, now_h, now_m):
    """
    Selects open stores. Collects the list of
    open stores else return empty list.
    Args:
        store_info (list): found stores on user's
                            request
        now (str): current user's time
    Returns:
        store_info (list): open stores
    """
    open_stores = []
    LOG.info(f" user's current time {now_h, now_m}")

    for store in store_info:
        # formating store's work hours 
        time_splited = store['hours'].split(' – ')
        open = time_refactoring(time_splited[0])
        close = time_refactoring(time_splited[1])
        LOG.info(f'formated_work_time {open, close}')

        if now_h == open[0]:
            if now_m >= open[1]:
                open_stores.append(store)
        elif now_h > open[0]:
            open_stores.append(store)
        elif now_h == close[0]:
            if now_m < close[1]:
                open_stores.append(store)
        elif now_h < close[0]:
            open_stores.append(store)
    LOG.info(f'open stores {open_stores}')            
    return open_stores