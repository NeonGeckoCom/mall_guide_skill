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


from neon_utils.skills.neon_skill import NeonSkill, LOG
from mycroft.skills.core import intent_file_handler
from .request_handling import RequestHandler
import re



class DirectorySkill(NeonSkill):

    def __init__(self):
        super(DirectorySkill, self).__init__(name="DirectorySkill")
        self.request_handler = RequestHandler()
        self.cache = dict()
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
        LOG.info(f"Message is {message.data}")
        if message.data == {}:
            self.speak('Message is empty')
            return None, None
        else:
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
        """
        Speaks shop info that was found.
        Substitutes time format for better pronunciation.
        speak_dialog('found_shop', {"name": shop['name'], "hours": hours, "location": location})
        Shows shop label image.
        Args:
            shop_info (list): found shops on user's
                                request
        """
        for shop in shop_info:
            LOG.info(shop)
            location = self.request_handler.location_format(shop['location'])
            hours = re.sub('(\d+)am(.+\d)pm', r'\1 A M \2 P M', shop['hours'])
            self.speak_dialog('found_shop', {"name": shop['name'], "hours": hours, "location": location})
            LOG.info({"name": shop['name'], "hours": hours, "location": location})
            self.gui.show_image(shop['logo'], caption=f'{hours} {location}', title=shop['name'])

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
        shops = self.request_handler.shop_selection_by_floors(floor, shop_info)
        if shops:
            self.speak_shops(shops)
            return 3, None
        else:
            self.speak_dialog('no_shop_on_level')
            self.speak_shops(shop_info)
            return 3, None

    def open_shops_search(self, shop_info):
        """
       Selects open shops. Collects the list of
       open shops else return empty list.
       Args:
           shop_info (list): found shops on user's
                               request
       Returns:
           shop_info (list): open shops
       """
        open_shops = []
        day_time, hour, min = self.request_handler.curent_time_extraction()
        LOG.info(f"User's time {day_time, hour, min}")
        for shop in shop_info:
            parse_time = shop['hours'].split('-')
            LOG.info(f'Parse time {parse_time}')
            open_time = int(re.sub('[^\d+]', '', parse_time[0]))
            close_time = int(re.sub('[^\d+]', '', parse_time[1]))
            if open_time <= hour < close_time:
                open_shops.append(shop)
        return open_shops


    def time_calculation(self, shop_info, open):
        # add logic if shop opens and closes not at am-pm time period
        """
        Calculates time difference between user's current time
        and shop working hours.
        If shop is closed and user is before opening speaks how
        much time is left for waiting. If user's time is evening
        speaks when the shop opens in the morning. In other cases
        just speaks shops info.
        If user in open hours, speak the shop info. If shop open
        and closes in one hour speaks how many minutes left.
        Args:
            shop_info (list): found shops on user's request
            open (boolean): True - if shop is open
        Returns:
         3, None (to ask for another shop info)
        Examples:
            work time 9am-10pm
            user's time 8am
            Prompt: 'Shop is closed now. Opens in 1 hour'
        """
        for shop in shop_info:
            work_time = shop['hours']
            LOG.info(f'work_time {work_time}')
            shop_name = shop['name']
            day_time, hour, min = self.request_handler.curent_time_extraction()
            parse_time = work_time.split('-')
            LOG.info(f'parse_time {parse_time}')
            open_time = int(re.sub('[^\d+]', '', parse_time[0]))
            close_time = int(re.sub('[^\d+]', '', parse_time[1]))
            # time left
            wait_h = open_time - hour - 1
            wait_min = 60 - min
            if open is True:
                if day_time[1] == 'pm' and 0 >= (close_time - hour) <= 1:
                    self.speak(f'{shop_name} closes in {wait_min} minutes.')
                else:
                    self.speak(f'{shop_name} is open.')
                self.speak_shops([shop])
            else:
                if day_time[1] == 'am' and hour < open_time:
                    if wait_h == 0:
                        self.speak(f'{shop_name} is closed now. Opens in {wait_min} minutes')
                    else:
                        self.speak(f'{shop_name} is closed now. Opens in {wait_h} hour and {wait_min} minutes')
                elif hour >= close_time:
                    self.speak(f'{shop_name} is closed now. Shop opens at {open_time}')
                self.speak_shops([shop])
        return 3, None

    def shops_by_time_selection(self, shop_info):
        """
        If user chose to select shops by time or
        use like default selection. Selects open
        shops.
        Args:
           shop_info (list): found shops on user's
                               request
        Returns:
           shop_info (list): open shops
        """
        LOG.info(f"Shop by time selection {shop_info}")
        open_shops = self.open_shops_search(shop_info)
        if len(open_shops) >= 1:
            return self.time_calculation(open_shops, True)
        else:
            return self.time_calculation(shop_info, False)

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
        LOG.info(str(user_request))
        LOG.info(str(mall_link))
        if user_request is not None:
            self.speak_dialog(f"I am parsing shops and malls for your request")
            LOG.info(f"I am parsing shops and malls for your request")
            shop_info = self.request_handler.get_shop_data(mall_link, user_request)
            LOG.info(f"I found {len(shop_info)} shops")
            LOG.info(f"shop list: {shop_info}")
            if len(shop_info) == 0:
                self.speak_dialog("shop_not_found")
                user_request = self.get_response('repeat')
                return 1, user_request
            elif len(shop_info) > 1:
                self.speak_dialog('more_than_one')
                # ask for the way of selection: time, location, nothing
                sorting_selection = self.get_response('Do you want to select'
                                                      'store by work hours or location?')
                if sorting_selection:
                    LOG.info(f'Users answer on sorting options: {sorting_selection}')
                    if 'time' in sorting_selection or 'hour' in sorting_selection:
                        LOG.info('Time sorting selected')
                        return self.shops_by_time_selection(shop_info)
                    elif 'location' in sorting_selection:
                        LOG.info('Location sorting selected')
                        return self.location_selection(shop_info)
                    elif 'no' in sorting_selection:
                        LOG.info('No sorting selected. Sorting by time on default.')
                        return self.shops_by_time_selection(shop_info)
                    else:
                        LOG.info('Nothing matched. Sorting by time on default.')
                        return self.shops_by_time_selection(shop_info)
            else:
                LOG.info(f"found shop {shop_info}")
                self.speak_shops(shop_info)
                return 3, None
        else:
            LOG.info(str(None))
            return 3, None

    def execute(self, user_request, mall_link):
        count = 0
        LOG.info('Start execute')
        while count < 3:
            LOG.info(str(user_request))
            LOG.info(str(mall_link))
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
