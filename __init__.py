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
from .request_handling import existing_lang_check, get_shop_data,\
                                shop_selection_by_floors,\
                                location_format,\
                                curent_time_extraction
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
        shops = shop_selection_by_floors(floor, shop_info)
        if shops:
            self.speak_shops(shops)
        else:
            self.speak_dialog('no_shop_on_level')
            self.speak_shops(shop_info)
        return 3, None

    def open_shops_search(self, shop_info, day_time, hour, min):
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
        LOG.info(f"User's time {day_time, hour, min}")
        for shop in shop_info:
            parse_time = re.findall(r'(\d+)+[am|pm]', shop['hours'])
            LOG.info(f'Parsed time {parse_time}')
            open_time = int(parse_time[0])
            close_time = int(parse_time[1])
            if open_time <= hour < close_time:
                open_shops.append(shop)
            elif day_time[1] == 'am' and open_time <= hour:
                open_shops.append(shop)
        return open_shops


    def time_calculation(self, shop_info, open, day_time, hour, min):
        # add logic if shop opens and closes not at am-pm time period
        # change to speak dialog
        """
        Calculates time difference between user's current time
        and shop working hours.
        If 'open' argument is True:
            If user one hour or less before closing: speaks how
                many minutes left. Speaks shop info.
            Else speaks corresponging dialog. 
            Speaks shop info.
        If 'open' argument is False:
            Speaks corresponding dialog.
            If user is one hour or less before opening hours 
                speaks how much time is left for waiting. 
            If user's time is 'am' and user is before opening
                hours, speaks how many hours and minutes left 
                waiting.
            If user's time is evening (pm) speaks when the shop 
                opens in the morning.
                Speaks shop info.
        Args:
            shop_info (list): found shops on user's request
            open (boolean): True - if shop is open
            day_time (str): user's current day time (am|pm) 
            hour (int): user's current hour
            min (int): user's current minute
        Returns:
            3, None (to ask for another shop info)
        Examples:
            work time 9am-10pm
            user's time 8am
            Prompt: 'Shop is closed now. Opens in 1 hour'
        """
        for shop in shop_info:
            work_time = shop['hours']
            normalized_time = re.findall(r'(\d+)[am|pm]', work_time)
            open_time = int(normalized_time[0])
            close_time = int(normalized_time[1])
            LOG.info(f'work_time {work_time}')
            shop_name = shop['name']
            parse_time = work_time.split('-')
            LOG.info(f'parse_time {parse_time}')
            # time left
            wait_h = open_time - hour - 1
            wait_min = 60 - min
            if open:
                if day_time[1] == 'pm' and 0 < (close_time - hour) <= 1:
                    LOG.info(f'{shop_name} closes in {wait_min} minutes.')
                    self.speak_dialog('closing_minutes', {"shop_name": shop_name, "wait_min": wait_min})
                else:
                    LOG.info(f'{shop_name} is open.')
                    self.speak_dialog('open_now', {'shop_name':  shop_name})
                LOG.info([shop])
                self.speak_shops([shop])
            else:
                if day_time[1] == 'am' and hour < open_time:
                    if wait_h == 0:
                        LOG.info(f'{shop_name} is closed now. Opens in {wait_min} minutes')
                        self.speak_dialog('opening_minutes', {"shop_name": shop_name, "wait_min": wait_min})
                    else:
                        LOG.info(f'{shop_name} is closed now. Opens in {wait_h} hour and {wait_min} minutes')
                        self.speak_dialog('opening_hours', {"shop_name": shop_name, "wait_h": wait_h, "wait_min": wait_min})
                elif hour >= close_time:
                    LOG.info(f'{shop_name} is closed now. Shop opens at {open_time}')
                    self.speak_dialog('closed_now', {'shop_name': shop_name, 'open_time': open_time})
                LOG.info([shop])
                self.speak_shops([shop])
        return 3, None

    def shops_by_time_selection(self, shop_info):
        """
        If user chose to select shops by time or
        use like default selection. Gets user's
        current time. Selects open shops. 
        Args:
           shop_info (list): found shops on user's
                               request
        Returns:
            time_calculation function with True 
                in 'open' argument.
            time_calculation function with False 
                in 'open' argument. (if list
                of open shops is 0)
           
        """
        LOG.info(f"Shop by time selection {shop_info}")
        day_time, hour, min = curent_time_extraction()
        # day_time, hour, min = ['11:15', 'pm'], 11, 15
        open_shops = self.open_shops_search(shop_info, day_time, hour, min)
        if len(open_shops) >= 1:
            return self.time_calculation(open_shops, True, day_time, hour, min)
        else:
            return self.time_calculation(shop_info, False, day_time, hour, min)

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
            self.speak_dialog("start_parsing")
            LOG.info(f"I am parsing shops and malls for your request")
            file_path = self.file_system.path
            LOG.info(f'file_path {file_path}')
            shop_info = get_shop_data(mall_link, user_request, file_path)
            LOG.info(f"I found {len(shop_info)} shops")
            LOG.info(f"shop list: {shop_info}")
            if len(shop_info) == 0:
                user_request = self.get_response('shop_not_found')
                return 1, user_request
            elif len(shop_info) > 1:
                self.speak_dialog('more_than_one')
                # ask for the way of selection: time, location, nothing
                sorting_selection = self.get_response('choose_selection')
                if sorting_selection:
                    LOG.info(f'Users answer on sorting options: {sorting_selection}')
                    if self.voc_match(sorting_selection, "time"):
                        LOG.info('Time sorting selected')
                        return self.shops_by_time_selection(shop_info)
                    elif self.voc_match(sorting_selection, "location"):
                        LOG.info('Location sorting selected')
                        return self.location_selection(shop_info)
                    elif self.voc_match(sorting_selection, "no"):
                        LOG.info('No sorting selected. Sorting by time on default.')
                        return self.shops_by_time_selection(shop_info)
                    else:
                        LOG.info('Nothing matched. Sorting by time on default.')
                        return self.shops_by_time_selection(shop_info)
            else:
                LOG.info(f"found shop {shop_info}")
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
