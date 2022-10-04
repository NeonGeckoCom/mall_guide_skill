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

from neon_utils.skills.neon_skill import LOG
from datetime import datetime
import re

def current_time_extraction():
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


def time_calculation(shop_info, day_time, hour, min):
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
        open_shops = []
        closed_shops = []
        for shop in shop_info:
            work_time = shop['hours']
            normalized_time = re.findall(r'(\d+)[am|pm]', work_time)
            open_time = int(normalized_time[0])
            close_time = int(normalized_time[1])
            LOG.info(f'work_time {work_time}')
            LOG.info(f'open_time {open_time},  close_time {close_time}')
            # time left
            wait_h = open_time - hour - 1
            wait_min = 60 - min
            if day_time[1] == 'pm' and 0 < (close_time - hour) <= 1:
                shop['open'] = 'open'
                open_shops.append([wait_min, None, shop])
            elif day_time[1] == 'pm' and close_time > hour:
                shop['open'] = 'open'
                open_shops.append([None, None, shop])
            elif day_time[1] == 'am' and open_time <= hour:
                shop['open'] = 'open'
                open_shops.append([None, None, shop])
            elif day_time[1] == 'am' and hour < open_time:
                if wait_h == 0:
                    shop['open'] = 'closed'
                    closed_shops.append([wait_min, None, shop])
                else:
                    shop['open'] = 'closed'
                    closed_shops.append([wait_min, wait_h, shop])
            elif day_time[1] == 'am' and hour >= close_time:
                shop['open'] = 'closed'
                closed_shops.append([None, open_time, shop])
        LOG.info(f'open and closed shops: {open_shops}, {closed_shops}')      
        found_shops = open_shops + closed_shops
        LOG.info(found_shops)
        return found_shops

