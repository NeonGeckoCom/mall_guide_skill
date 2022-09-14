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

import re

from mycroft.skills.core import intent_file_handler
from neon_utils.skills.neon_skill import LOG, NeonSkill

from .request_handling import RequestHandler


class DirectorySkill(NeonSkill):

    def __init__(self):
        super(DirectorySkill, self).__init__(name="DirectorySkill")
        self.request_handler = RequestHandler()
        self.from_hashed_stores = []


    def initialize(self):
        # When first run or prompt not dismissed, wait for load and prompt user
        if self.settings.get('prompt_on_start'):
            self.bus.once('mycroft.ready', self._start_mall_parser_prompt)

    @intent_file_handler("run_mall_parser.intent")
    def start_mall_parser_intent(self, message):
        LOG.info(message.data)

        self._start_mall_parser_prompt(message)
        return

    # @property
    def mall_link(self):
        mall_link = 'https://www.alamoanacenter.com/'
        return self.settings.get("mall_link") or mall_link

    def user_request_handling(self, message):
        LOG.info(f"Message is {message.data}")
        request_lang = message.data['lang'].split('-')[0]
        user_request = message.data['shop']
        LOG.info(f"{self.mall_link()}")
        LOG.info(str(request_lang))
        LOG.info(user_request)
        found, link = RequestHandler.existing_lang_check(request_lang, self.mall_link())
        if found:
            link = self.mall_link()+request_lang+'/directory/'
            LOG.info('new link: '+ link)
            return user_request, link
        else:
            self.speak_dialog("no_lang")
            return None, None

    def start_again(self):
        start_again = self.ask_yesno("ask_more")
        if start_again == "yes":
            another_shop = self.get_response('another_shop')
            if another_shop is not None:
                LOG.info(f'another shop {another_shop}')
                return another_shop
            else:
                return None
        elif start_again == "no":
            self.speak_dialog('no_shop_request')
            return None
        else:
            self.speak_dialog('unexpected_error')
            return None

    def speak_shops(self, shop_info):
        for shop in shop_info:
            LOG.info(shop)
            location = self.request_handler.location_format(shop['location'])
            #add pronounce_number
            hours = re.sub('(\d+)am(.+\d)pm', r'\1 A M\2 P M', shop['hours'])
            self.speak_dialog('found_shop', {"name": shop['name'], "hours": hours, "location": location})
            self.speak_dialog({"name": shop['name'], "hours": hours, "location": location})
            self.time_calculation(self, hours, shop['name'])
            #self.gui.show_image(shop['logo'])
        return 3, None

    def more_than_one(self, shop_info):
        self.speak_dialog('more_than_one')
        speak_all_shops = self.ask_yesno('speak_all_shops')
        if speak_all_shops == 'yes':
            self.speak_dialog('all_locations')
            return self.speak_shops(shop_info)
        else:
            shop_by_floor = self.ask_yesno('shop_by_floor')
            if shop_by_floor == 'yes':
                floor = self.get_response('which_floor')
                shop = self.request_handler.shop_selection_by_floors(floor, shop_info)
                if shop is not None:
                    return self.speak_shops([shop])
                else:
                    self.speak_dialog('no_shop_on_level')
                    return self.speak_shops(shop_info)
            else:
                self.speak_dialog('all_locations')
                return self.speak_shops(shop_info)

    def time_calculation(self, work_time, shop_name):
        # add logic if shop opens and closes not at am-pm time period
        """
        Calculates time difference between user's current time 
        and shop working hours. Returns certain prompt.
        If user is before opening speaks how much time 
        is left for waiting.
        If shop closes in one hour speaks how many minutes left.
        If user in open hours, tells that shop is open.
        If user after closing hour, tells that shop is closed,
        tells opening time.
        Args:
            work_time (str): work hours from found shop data
            shop_name (str): shop name from found shop data
                
        Examples:
            work time 9am-10pm
            user's time 8am
            Ptompt: 'Shop is closed now. Opens in 1 hour'
        """
        day_time, hour, min = self.request_handler.curent_time_extraction()
        parse_time = work_time.split('-')
        open_time = int(re.sub('[^\d+]', '',parse_time[0]))
        close_time = int(re.sub('[^\d+]', '',parse_time[1]))
        # time left
        wait_h = open_time-hour-1
        wait_min = 60-min
        if day_time[1]=='am' and hour<open_time:
            self.speak(f'{shop_name} is closed now. Opens in {wait_h} hour and {wait_min} minutes')
        elif day_time[1]=='pm' and close_time-hour <= 1:
            self.speak(f'{shop_name} closes in {wait_min} minutes')
        elif hour>open_time and hour<close_time:
            self.speak(f'{shop_name} is open now.')
        elif hour>=close_time:
            self.speak(f'{shop_name} is closed now. Shop opens at {open_time}')
        else:
            # change this else variant
            self.speak_dialog(f'{shop_name} is open now.')

    
    def find_shop(self, user_request, mall_link):
        LOG.info(str(user_request))
        LOG.info(str(mall_link))
        if user_request is not None:
            self.speak_dialog(f"I am parsing shops and malls in your request")
            LOG.info(f"I am parsing shops and malls in your request")
            shop_info = self.request_handler.get_shop_data(mall_link, user_request)
            if len(shop_info) == 0:
                self.speak_dialog("shop_not_found")
                user_request = self.get_response('repeat')
                return 1, user_request
            elif len(shop_info) > 1:
                return self.more_than_one(shop_info)
            else:
                LOG.info(f"found shop {shop_info}")
                return self.speak_shops(shop_info)
        else:
            LOG.info(str(None))
            return 3, None

    def execute(self, user_request, mall_link):
        count = 0
        user_request = user_request
        LOG.info('Start execute')
        while count < 3:
            LOG.info(str(user_request))
            LOG.info(str(mall_link))
            new_count, user_request = self.find_shop(user_request, mall_link)
            count = count + new_count
        # here is some logic problem (big pause after 3 tries)
        user_request = self.start_again()
        LOG.info(str(user_request))
        if user_request is not None:
            LOG.info('New execution')
            self.execute(user_request, mall_link)
        else:
            return None

    def _start_mall_parser_prompt(self, message):
            LOG.info('Prompting Mall parsing start')
            self.make_active()
            if message is not None:
                LOG.info('new message'+str(message))
                user_request, mall_link = self.user_request_handling(message)
                LOG.info(mall_link)
                if user_request is not None:
                    if self.execute(user_request, mall_link) is not None:
                        LOG.info('executed')
                        return
                    else:
                        self.speak_dialog('finished')
                else:
                    self.speak_dialog('finished')
            


def create_skill():
    return DirectorySkill()
