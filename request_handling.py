# NEON AI (TM) SOFTWARE, Software Development Kit & Application Framework
# All trademark and other rights reserved by their respective owners
# Copyright 2008-2022 Neongecko.com Inc.
# Contributors: Daniel McKnight, Guy Daniels, Elon Gasper, Richard Leeds,
# Regina Bloomstine, Casimiro Ferreira, Andrii Pernatii, Kirill Hrymailo
# BSD-3 License
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS  BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA,
# OR PROFITS;  OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE,  EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from urllib.error import HTTPError
import requests
import bs4
from neon_utils.skills.neon_skill import LOG
import urllib.request

import lingua_franca
from lingua_franca.format import pronounce_number
lingua_franca.load_language('en')

import re
import os
import json

from datetime import datetime


class RequestHandler():
        
    caching_file = ''

def find_cached_stores(user_request: str, url, file_path):
    """
    Check shop name existence in cache keys
    Args:
        user_request (str): shop from user's message
    Returns:
        if file is empty -> None, {}
        if shop wasn't found -> None, read data
        if shop found ->  store_info (list), read data
    Examples:
        [
        {"name": "ABS stores", "time": "8am-10pm", "location": "1 level"},
        {"name": "ABS stores", "time": "8am-10pm", "location": "2 level"}
        ]
    """
    caching_file = file_path+'/cached_stores.json'
    if os.path.isfile(caching_file) == False:
        LOG.info("Cache file doesn't exist")
        caching_stores_in_mall(file_path, url)
        return find_cached_stores(user_request, url, file_path)
    else:
        with open(caching_file, 'r', encoding='utf-8') as readfile:
            data = json.load(readfile)
            found_key = [key for key in data.keys() 
                            if key.lower() in user_request.lower() 
                                or user_request.lower() in key.lower()]
            LOG.info(f'found key {found_key}')
            if len(found_key) >=1 :
                store_name = str(found_key[0])
                LOG.info(f'Shop exists {data[store_name]}')
                return data[store_name], data
            else:
                LOG.info("Shop doesn't exist in cache")
                return None, data

def caching_stores_in_mall(file_path, url):
    """
    Creates caching file in the current class.
    Creates empty dictionary for cache. Parses
    all shops info. Creates dict key from shop
    name. Value list of dicts with current shop
    info.
    If shop name already exists in created dict
        append current shop dict to existing 
        list.
    Writes created dict to created JSON file.
    Args:
        file_path (str): new file path
        url (str): malls url
    Examples:
        {"ABS stores": [
        {"name": "ABS stores", "time": "8am-10pm", "location": "1 level"},
        {"name": "ABS stores", "time": "8am-10pm", "location": "2 level"}
        ]}
    """
    caching_file = file_path+'/cached_stores.json'
    LOG.info(f'caching_file {caching_file}')
    shop_cache = {}
    soup = parse(url)
    for shop in soup.find_all(attrs={"class": "directory-tenant-card"}):
            logo = shop.find_next("img").get('src')
            info = shop.find_next(attrs={"class": "tenant-info-container"})
            name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
            hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
            location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
            shop_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
            if name in shop_cache.keys():
                shop_cache[name].append(shop_data)                
            else:
                shop_cache[name] = [shop_data]
    with open(caching_file,
                                'w+') as outfile:
        json.dump(shop_cache, outfile, ensure_ascii=False)
    os.chmod(caching_file, 777)
    LOG.info("Created mall's cache")

def existing_lang_check(user_lang: str, url):
    """
    Check existence of user's language
    on the mall web-page
    Args:
        user_lang (str): user's lang in ISO 639-1
    Returns:
        bool: True if lang exists
    """
    link = url+user_lang+'/directory/'
    response = requests.get(link)
    if response.status_code == 200:
        LOG.info('This language is supported')
        return True, link
    else:
        LOG.info('This language is not supported')
        return False, link

def curent_time_extraction():
    """
    Defines current time in utc timezone
    Format: hour:minutes part of day (1:23 pm)

    Returns:
        day_time (list): contains splited time
                            numerals and part of the day
                            day_time -> ['07:19', 'am']
        hour (int): current hour
        min (int): current minute
    """
    now = datetime.now().time().strftime("%I:%M %p")
    # now = datetime.today().strftime("%H:%M %p")
    LOG.info(f'now {now}')
    day_time = now.lower().split(' ')
    exact_time = day_time[0].split(':')
    hour, min = int(exact_time[0]), int(exact_time[1])
    return day_time, hour, min

def location_format(location):
    """
    Finds all digits in store's location and
    formats them to numeral words.
    Args:
        location (str): location info
        from shops info
    Returns:
        if digits were found:
            pronounced (str): utterance with
            pronounced digits
        else:
            location (str): not changed utterance
    Examples:
        'level 1' -> 'level one'
    """
    floor = re.findall(r'\d+', location)
    if len(floor) > 0:
        floor = floor[0]
        num = pronounce_number(int(floor), ordinals=False)
        pronounced = re.sub(r'\d+', num, location)
        return pronounced
    else:
        return location

def shop_selection_by_floors(user_request, found_shops):
    """
    If there are several shops in found shops list
    and user agrees to select shop by floor.
    Finds all digits in store's location and
    formats them to ordinal and cardinal numerals.
    Matches formated numerals with user's request.
    If shop was found appends it to the new found
    list.
    Args:
        user_request (str): floor from user
        found_shops (list): found shops on user's
        request
    Returns:
        shops_by_floor (list): shops that was found by floor
    """
    shops_by_floor = []
    for shop in found_shops:
        numbers = re.findall(r'\d+', shop['location'])
        if len(numbers) > 0:
            numbers = numbers[0]
            num = pronounce_number(int(numbers), ordinals=False)
            num_ordinal = pronounce_number(int(numbers), ordinals=True)
            if num in user_request or num_ordinal in user_request:
                shops_by_floor.append(shop)
    return shops_by_floor

def parse(url):
    headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
        }
    request = urllib.request.Request(url,
                                    headers=headers)
    try:
        with urllib.request.urlopen(request) as page:
            soup = bs4.BeautifulSoup(page.read(), features='lxml')
            return soup
    except HTTPError:
        LOG.info("Failed url parsing")


def get_shop_data(url, user_request, file_path):
    """
    Check existence of user's request store in cache
    if shop was found returns list with shop info,
    else does parsing of mall's web-page.
    Matches the name of existing stores with user's
    request. If store was found, returns list with
    stores' info and does caching, else returns empty
    list.
    on the mall web-page
    Args:
        url (str): mall link from hardcoded in init.py
        user_request (str): utterance from stt parsing
    Returns:
        : found_shops (list): found shops' info
    """
    # search for store existence in cache
    LOG.info(file_path)
    found_shops, data = find_cached_stores(user_request, url, file_path)
    LOG.info(found_shops)
    if found_shops:
        LOG.info(f"found_shops: {found_shops}")
        return found_shops
    else:
        return []

