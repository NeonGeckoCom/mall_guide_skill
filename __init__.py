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

import os


class MallParserSkill(NeonSkill):

    def __init__(self):

        super(MallParserSkill, self).__init__(name="MallParserSkill")
        self.script_path = os.path.join(os.path.dirname(__file__),
                                        'mall')
        self.request_handler = object

    def initialize(self):
        # When first run or prompt not dismissed, wait for load and prompt user
        if self.settings.get('prompt_on_start'):
            self.bus.once('mycroft.ready', self._start_mall_parser_prompt)

    @intent_file_handler("run_mall_parser.intent")
    def start_mall_parser_intent(self, message):
        LOG.info(message.data)

        self._start_mall_parser_prompt(message)
        return

    def finish(self):
        self.speak_dialog("finished")

    def repeat(self):
        self.speak_dialog("repeat")

    def no_lang(self):
        self.speak_dialog("no_lang")

    def what_shop(self):
        user_request = self.get_response("what_shop")
        return user_request

    def select(self, variants):
        self.speak_dialog('more_than_one')
        choice = self.get_response(variants)
        return choice

    def disambiguation_handling(self, shop_info):
        found_shops = []
        for shop in shop_info:
            found_shops.append(shop['name'])
        choice = self.select(found_shops)
        selected_shop = [shop for shop in shop_info if choice in shop['name']]
        return selected_shop

    def speak_shop_data(self, shop_data):
        self.speak(shop_data)

    def user_request_handling(self, message):
        tries = 0
        LOG.info(f"Message is {message.data}")
        request_lang = message.data['lang'].split('-')[0]
        mall_link = message.data['mall_link']
        user_request = message.data['utterance']
        while tries <= 3:
            if RequestHandler.existing_lang_check(request_lang, mall_link):
                return user_request, mall_link
            else:
                self.no_lang()
                user_request = self.get_response("repeat")
        else:
            return None, None

    def execute(self, message):
        count = 0
        user_request, mall_link = self.user_request_handling(message)
        if user_request is None:
            self.finish()
        else:
            user_request = self.what_shop()
            while count != 3:
                if user_request is not None:
                    self.speak_dialog(f"I am parsing shops and malls for your request")
                    shop_info = RequestHandler.get_shop_data(mall_link, user_request)
                    if shop_info is []:
                        self.speak_dialog("shop_not_found")
                        self.repeat()
                    elif len(shop_info) > 1:
                        selected_shop = self.disambiguation_handling(shop_info)
                        self.speak_shop_data(selected_shop)
                    else:
                        self.speak_shop_data(shop_info)
                        start_again = self.ask_yesno("ask_more")
                        if start_again == "yes":
                            self.execute(message)
                            return
                        else:
                            self.finish()
                else:
                    user_request = self.get_response("repeat")
                    count += 1

    def _start_mall_parser_prompt(self, message):
        if self.neon_in_request(message):
            LOG.info('Prompting Mall parsing start')
            self.make_active()
            start_parsing = self.ask_yesno("start")
            if start_parsing == "yes":
                self.execute(message)
                return
            else:
                repeat_instr = self.ask_yesno("stop")
                if repeat_instr == 'yes':
                    self.speak_dialog('finished')
                else:
                    self.execute(message)
                    return


def create_skill():
    return MallParserSkill()
