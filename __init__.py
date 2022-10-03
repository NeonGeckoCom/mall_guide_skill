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


from fileinput import close
from neon_utils.skills.neon_skill import NeonSkill, LOG
from mycroft.skills.core import intent_file_handler
from .request_handling import existing_lang_check, get_shop_data,\
                                shop_selection_by_floors,\
                                location_format
                                

from .time_calculations_handling import current_time_extraction,\
                                        time_calculation

import re



class DirectorySkill(NeonSkill):

    def __init__(self):
        super(DirectorySkill, self).__init__(name="DirectorySkill")
        self.url = "https://www.alamoanacenter.com/en/directory/"


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
        """
        Checks user language existence on mall's web-page
        using existing_lang_check() function.
        Returns:
            None, None: if message is empty
            None, None: if language is not supported
            user_request, link (str, str): if language exists
            answer)
        """
        LOG.info(f"Message is {message.data}")
        if message.data == {} or message is None:
            return None, None
        else:
            request_lang = self.lang.split('-')[0]
            user_request = message.data['shop']
            LOG.info(f"{self.mall_link()}")
            LOG.info(str(request_lang))
            LOG.info(user_request)
            found, link = existing_lang_check(request_lang, self.mall_link())
            if found:
                link = self.mall_link()+request_lang+'/directory/'
                LOG.info('new link: '+ link)
                return user_request, link
            else:
                self.speak_dialog("no_lang")
                return None, None

    def start_again(self):
        """
        Asks yes/no question whether user wants to
        get another shop info, after Neon gave the
        information about previously selected shop.
        If user's answer 'yes': asks what shop is
        needed. Returns user's answer.
        If 'no', speaks corresponding dialog.
        If some other answer, speaks corresponding
        dialog
        Returns:
            None (if no shop in request, if user's
            answer is 'no', if user gives some other
            answer)
        """
        start_again = self.ask_yesno("ask_more")
        if start_again == "yes":
            another_shop = self.get_response('another_shop')
            if another_shop is not None:
                LOG.info(f'another shop {another_shop}')
                return another_shop
        elif start_again == "no":
            self.speak_dialog('no_shop_request')
        else:
            self.speak_dialog('unexpected_error')
        return None

    def speak_shops(self, shop_info):
        """
        Speaks shop info that was found.
        Substitutes time format for better pronunciation.
        speak_dialog('found_shop', {"name": shop['name'], "hours": hours, "location": location})
        Shows shop label image in gui.
        Args:
            shop_info (list): found shops on user's
                                request
        """
        for shop in shop_info:
            LOG.info(shop)
            location = location_format(shop['location'])
            hours = re.sub('(\d+)am.+(\d+)pm', r'from \1 A M to \2 P M', shop['hours'])
            self.speak_dialog('found_shop', {"name": shop['name'], "hours": hours, "location": location})
            LOG.info({"name": shop['name'], "hours": hours, "location": location})
            # self.gui.show_image(shop['logo'], caption=f'{hours} {location}', title=shop['name'])

    def location_selection(self, shop_info):
        """
        If there are several shops in found shops list
        and user wants to get shop info on the certain
        floor. If shop on that floor exists speaks
        this shop info. Else speaks all shops info.
        Args:
            shop_info (list): found shops on user's
                                request
        Returns:
            3, None (to ask for another shop info)
        """
        LOG.info(f"Shop by location selection {shop_info}")
        floor = self.get_response('which_floor')
        shops = shop_selection_by_floors(floor, shop_info)
        if shops:
            self.speak_shops(shops)
        else:
            self.speak_dialog('no_shop_on_level')
            #To do: the nearest shop search
            self.speak_dialog('all_locations', {'n':len(shop_info), 'store_name':shop_info[0]['name']})
            self.speak_shops(shop_info)
        return 3, None

    def speak_in_time_order(self, shop, open_info):
        if open_info:
            if shop[0]:
                self.speak_dialog('closing_minutes', {'closing_minutes': open[0][0]})
            self.speak_shops([shop[2]])
        else:
            if shop[0] and shop[1]:
                self.speak_dialog('opening_hours', {'wait_h': shop[1], 'wait_min': shop[0]})
            elif shop[0]:
                self.speak_dialog('opening_minutes', {'wait_min': shop[0]})
            self.speak_shops([shop[2]])

    def first_from_many_by_time(self, open, closed):
        LOG.info(f'open: {open}, closed: {closed}')
        first_shop = []
        if len(open) != 0:
            first_shop = open[0]
            self.speak_dialog('open_now', {'shop_name': first_shop[2]['name']})
            self.speak_in_time_order(first_shop, True)
        else:
            first_shop = closed[0]
            self.speak_dialog('closed_now', {'shop_name': first_shop[2]['name']})
            self.speak_in_time_order(first_shop, False)
        return first_shop

    def other_shops_by_time(self, open, closed, first_shop):
        if first_shop in open:
            for shop in open[1:]:
                self.speak_in_time_order(shop, True)
            if len(closed) != 0:
                self.speak_dialog('closed_now', {'shop_name': open[0][2]['name']})
                for shop in closed[1:]:
                    self.speak_in_time_order(shop, False) 
        else:
            for shop in close[1:]:
                self.speak_in_time_order(shop, True)
        return 3, None
        
    def find_shop(self, user_request, mall_link):
        """
        When the intent is matched, user_request
        variable contains the name of the shop.
        The matching function get_shop_data() is
        used to find the shop name in cache or
        on the mall page.
        If user's request is not None this function
        can return several shops, one shop or empty
        list.
        If no shop was found asks user to repeat.
        returns 1, user_request to continue the
        execution loop in self.execute().
        If there are several shops asks user what way
        of sorting to choose: time, level, nothing.
            If 'time' - finds open shops. If open shops
            list is not empty speaks open shops, else
            tells time difference between user and shops'
            work hours.
            If 'location' - asks what level user is interested
            in. If shops were found speaks shops' info,
            else tells that there is no shop on that level
            and speaks all found shops.
            If  'no' - sorts by time.
            If nothing matched in the answer - sorts by time.
        If there was one shop found speaks this
        shop info. Returns 3, None to stop current
        shop search.
        Location and time sorting functions return
        3, None to stop current shop search.
        """
        LOG.info(f'user_request {user_request}')
        LOG.info(f'mall_link {mall_link}')
        if user_request is not None:
            file_path = self.file_system.path
            LOG.info(f'file_path {file_path}')
            shop_info = get_shop_data(mall_link, user_request, file_path)
            LOG.info(f"shop list: {shop_info}")
            day_time, hour, min = current_time_extraction()
            if len(shop_info) == 0:
                user_request = self.get_response('shop_not_found')
                return 1, user_request
            elif len(shop_info) > 2:
                LOG.info(f"more_than_two: n = {len(shop_info)}, store {shop_info[0]['name']}")
                self.speak_dialog('more_than_two', {'n': len(shop_info), 'store': shop_info[0]["name"]})
                # contains lists of open and closed shops
                open, closed = time_calculation(shop_info, day_time, hour, min)
                # speak first shop
                first_shop = self.first_from_many_by_time(open, closed)
                more_info = self.ask_yesno('more_shops_info')
                if more_info == 'yes':
                    # ask for the way of selection: time, location, nothing
                    sorting_selection = self.get_response('choose_selection')
                    if sorting_selection:
                        LOG.info(f'Users answer on sorting options: {sorting_selection}')
                        if self.voc_match(sorting_selection, "time"):
                            return self.other_shops_by_time(open, closed, first_shop)
                        elif self.voc_match(sorting_selection, "location"):
                            LOG.info('Location sorting selected')
                            return self.location_selection(shop_info)
                        elif self.voc_match(sorting_selection, "no"):
                            LOG.info('No sorting selected. Sorting by time on default.')
                            return self.other_shops_by_time(open, closed, first_shop)
                        else:
                            LOG.info('Nothing matched. Sorting by time on default.')
                            return self.other_shops_by_time(open, closed, first_shop)
            else:
                LOG.info(f"found shop {shop_info}")
                self.speak('I found')
                self.speak_shops(shop_info)
        return 3, None

    def execute(self, user_request, mall_link):
        count = 0
        LOG.info('Start execute')
        while count < 3 and user_request is not None and mall_link is not None:
            new_count, user_request = self.find_shop(user_request, mall_link)
            count = count + new_count
        user_request = self.start_again()
        LOG.info(str(user_request))
        if user_request is not None:
            LOG.info('New execution')
            self.execute(user_request, mall_link)
        else:
            return None

    def _start_mall_parser_prompt(self, message):
        if self.neon_in_request(message):
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
        else:
            return
            


def create_skill():
    return DirectorySkill()
