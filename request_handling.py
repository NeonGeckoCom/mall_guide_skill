from urllib.error import HTTPError
import requests
import bs4
from os import path
from neon_utils.skills.neon_skill import LOG
import urllib.request

import lingua_franca
from lingua_franca import parse
from lingua_franca.format import pronounce_number
lingua_franca.load_language('en')

from datetime import datetime
import pytz
import re


class RequestHandler():

    def __init__(self) -> None:
        self.hashing_file = path.join(path.abspath(path.dirname(__file__)),
                                  'hashed_stores.txt')
        

    def existing_lang_check(user_lang, url):
        link = url+user_lang+'/directory/'
        response = requests.get(link)
        if response.status_code == 200:
            LOG.info('This language is supported')
            return True, link
        else:
            LOG.info('This language is not supported')
            return False, link

    def parse(self, url):
        url = "https://www.alamoanacenter.com/en/directory/"
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

    def location_format(self, location):
        """
        Extracts numbers from string.
        Substitutes numerals from shop location data to words

        Args:
            locaion (str): location from mall parsing

        Returns:
            pronounced (str): location with pronounced numerals 

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
            location

    def save_stores_data(self, store_info):
        # initial hashing implementation
        with open(self.hashing_file, 'a+', encoding="utf-8") as hashed_file:
            hashed_file.write(str(store_info)+'\n')

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

    def clear_request(self, user_request):
        """
        Cleares user request from unnecessary after intent is trigered but
        shop name was not recognized. 

        Args:
            user_request (str): utterance from stt

        Returns:
            user_request (str): cleared utterance
                
        Examples:
            'find starbucks' -> 'starbucks'
        """
        cleaned_request = re.sub('find|fine|where|is|are|I|i|can|could|help|me|looking|look|for|am', '', user_request)
        cleaned_request = cleaned_request.strip()
        return cleaned_request

    def get_shop_data(self, url, user_request):
        # Change hashing to json file
        LOG.info("Using cached stores data")
        with open(self.hashing_file, 'r+', encoding="utf-8") as from_hashed_file:
            self.from_hashed_stores = from_hashed_file.readlines()
            found_shops = [shop for shop in self.from_hashed_stores if str(user_request) in shop]
            if len(found_shops) != 0:
                LOG.info("Shop found in cached stores data")
                return found_shops
            else:
                found_shops = []
                soup = self.parse(url)
                for shop in soup.find_all(attrs={"class": "directory-tenant-card"}):
                    logo = shop.find_next("img").get('src')
                    info = shop.find_next(attrs={"class": "tenant-info-container"})
                    name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
                    if name.lower() in user_request.lower() or user_request.lower() in name.lower():
                        hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
                        location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
                        shop_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
                        found_shops.append(shop_data)
                for shop in found_shops:
                    self.save_stores_data(shop)
                return found_shops


    def shop_selection_by_floors(self, user_request, found_shops):
        for shop in found_shops:
            numbers = re.findall(r'\d+', shop['location'])
            if len(numbers) > 0:
                numbers = numbers[0]
                num = pronounce_number(int(numbers), ordinals=False)
                num_ordinal = pronounce_number(int(numbers), ordinals=True)
                if num in user_request or num_ordinal in user_request:
                    return shop
            else:
                None

