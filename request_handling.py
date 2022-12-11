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

import os
import json


class RequestHandler():
        
    caching_file = ''


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

#caching stores' info
def find_cached_stores(user_request: str, url, file_path):
    """
    Check store name existence in cache keys
    Args:
        user_request (str): store from user's message
    Returns:
        if file is empty -> None, {}
        if store wasn't found -> None, read data
        if store found ->  store_info (list), read data
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
                LOG.info(f'Store exists {data[store_name]}')
                return data[store_name], data
            else:
                LOG.info("Store doesn't exist in cache")
                return None, data

def caching_stores_in_mall(file_path, url):
    """
    Creates caching file in the current class.
    Creates empty dictionary for cache. Parses
    all stores info. Creates dict key from store
    name. Value list of dicts with current store
    info.
    If store name already exists in created dict
        append current store dict to existing 
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
    store_cache = {}
    soup = parse(url)
    for store in soup.find_all(attrs={"class": "directory-tenant-card"}):
            logo = store.find_next("img").get('src')
            info = store.find_next(attrs={"class": "tenant-info-container"})
            name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
            hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
            location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
            store_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
            if name in store_cache.keys():
                store_cache[name].append(store_data)                
            else:
                store_cache[name] = [store_data]
    with open(caching_file,
                                'w+') as outfile:
        json.dump(store_cache, outfile, ensure_ascii=False)
    os.chmod(caching_file, 777)
    LOG.info("Created mall's cache")

# mall link parsing
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


def get_store_data(url, user_request, file_path):
    """
    Check existence of user's request store in cache
    if store was found returns list with store info,
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
        : found_stores (list): found stores' info
    """
    # search for store existence in cache
    LOG.info(file_path)
    found_stores, data = find_cached_stores(user_request, url, file_path)
    LOG.info(found_stores)
    if found_stores:
        LOG.info(f"found_stores: {found_stores}")
        return found_stores
    else:
        return []

