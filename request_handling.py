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
from lingua_franca import parse
from lingua_franca.format import pronounce_number
lingua_franca.load_language('en')

import re
import os
from os import path
import json

from datetime import datetime
import pytz


class RequestHandler():

    def __init__(self) -> None:
        self.caching_file = path.join(path.abspath(path.dirname(__file__)),
                                  'cached_stores.json')

    def find_cached_stores(self, user_request: str):
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
        with open(self.caching_file, 'r') as readfile:
            file_length = os.stat(self.caching_file).st_size
            if file_length == 0:
                LOG.info('No shop in cache')
                return None, {}
            else:
                data = json.load(readfile)
                found_key = [key for key in data.keys() if key in user_request or user_request in key]
                if user_request is []:
                    LOG.info("Shop doesn't exist in cache")
                    return None, data
                else:
                    LOG.info('Shop exists')
                    return data[found_key], data

    def caching_stores(self, data, store_info: list):
        """
        Saves dictionary to JSON file
        key - shop name, value: list with shops info
        if file is empty -> creates dictionary
        if file contains info -> updates data dictionary
        with the new shop info
        Args:
            data (dict): existing shops info
            store_info (list): scraped store info
        Returns:
            store_info (list): scraped store info
        Examples:
            {"ABS stores": [
            {"name": "ABS stores", "time": "8am-10pm", "location": "1 level"},
            {"name": "ABS stores", "time": "8am-10pm", "location": "2 level"}
            ]}
        """
        if data == {}:
            for store in store_info:
                data = {store['name']: store}
                if data != {}:
                    new_store = {store['name']: store}
                    data.update(new_store)
        else:
            new_store = {store_info['name']: store_info}
            data.update(new_store)
        with open(self.caching_file, 'w') as outfile:
            json.dump(data, outfile)
        return store_info

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

    def curent_time_extraction(self):
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
        now = datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%H:%M %p")
        day_time = now.lower().split(' ')
        exact_time = day_time[0].split(':')
        hour, min = int(exact_time[0]), int(exact_time[1])
        return day_time, hour, min

    def location_format(self, location):
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

    def shop_selection_by_floors(self, user_request, found_shops):
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

    def parse(self, url):
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


    def get_shop_data(self, url, user_request):
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
        found_shops, data = self.find_cached_stores(user_request)
        if found_shops is not None:
            return found_shops
        else:
            # parsing mall web-page
            found_shops = []
            soup = self.parse(url)
            # loop through store names
            for shop in soup.find_all(attrs={"class": "directory-tenant-card"}):
                logo = shop.find_next("img").get('src')
                info = shop.find_next(attrs={"class": "tenant-info-container"})
                name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
                # matching store names with user's request
                if name.lower() in user_request.lower() or user_request.lower() in name.lower():
                    hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
                    location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
                    shop_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
                    found_shops.append(shop_data)
            if found_shops:
                # caching if shop was found
                self.caching_stores(data, found_shops)
                return found_shops
            else:
                # return empty list
                return found_shops

