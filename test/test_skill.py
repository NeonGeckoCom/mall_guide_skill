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

import shutil
import unittest

from os import mkdir
from os.path import dirname, join, exists
from mock import Mock
from ovos_utils.messagebus import FakeBus

from mycroft.skills.skill_loader import SkillLoader
from mycroft_bus_client import Message

import lingua_franca
lingua_franca.load_language('en')


class TestSkill(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        bus = FakeBus()
        bus.run_in_thread()
        skill_loader = SkillLoader(bus, dirname(dirname(__file__)))
        skill_loader.load()
        cls.skill = skill_loader.instance

        # Define a directory to use for testing
        cls.test_fs = join(dirname(__file__), "skill")
        if not exists(cls.test_fs):
            mkdir(cls.test_fs)
        
        # Override the configuration and fs paths to use the test directory
        cls.skill.settings_write_path = cls.test_fs
        cls.skill.file_system.path = cls.test_fs
        cls.skill._init_settings()
        # cls.skill.initialize()

        # Override speak and speak_dialog to test passed arguments
        cls.skill.speak = Mock()
        cls.skill.speak_dialog = Mock()
        

    def setUp(self):

        class MockGui:
            def __init__(self):
                self._data = dict()
                self.show_image = Mock()

            def __setitem__(self, key, value):
                self._data[key] = value

            def __getitem__(self, item):
                return self._data[item]

            @staticmethod
            def clear():
                pass  
        
        self.skill.speak.reset_mock()
        self.skill.speak_dialog.reset_mock()

        mock_gui = MockGui()
        self.skill.gui = mock_gui


    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.test_fs)

    def test_en_skill_init(self):

        self.skill.ask_yesno = Mock(return_value="yes")
        
        message = Message('test', {'utterance': 'find ABC stores',
                                   'store': 'ABC stores',
                                   'lang': 'en-us'},
                          {'context_key': 'MallParsing'})
        self.skill.user_request_handling(message)


    def test_en_time_calculation(self):
        store_info = [{'name': 'ABC Stores', 'hours': '9:30am – 9pm', 'location': 'Street Level 1, near Centerstage',
                      'logo': 'https://gizmostorageprod.blob.core.windows.net/tenant-logos/1615937914061-abcstores.png'},
                     {'name': 'ABC Stores', 'hours': '10:30am – 8:30pm', 'location': 'Street Level 1, in the Ewa Wing',
                      'logo': 'https://gizmostorageprod.blob.core.windows.net/tenant-logos/1615937946329-abcstores.png'}]

        now_hour, now_min = 9, 30
        open = True

        result = self.skill.time_calculation(store_info, open, now_hour, now_min)
        self.assertEqual(result, (3, None))

    def test_en_stores_by_time_selection(self):
        store_info = [{'name': 'ABC Stores', 'hours': '9:30am – 9pm', 'location': 'Street Level 1, near Centerstage',
                      'logo': 'https://gizmostorageprod.blob.core.windows.net/tenant-logos/1615937914061-abcstores.png'},
                     {'name': 'ABC Stores', 'hours': '10:30am – 8:30pm', 'location': 'Street Level 1, in the Ewa Wing',
                      'logo': 'https://gizmostorageprod.blob.core.windows.net/tenant-logos/1615937946329-abcstores.png'}]

        result = self.skill.stores_by_time_selection(store_info)
        self.assertEqual(result, (3, None))


if __name__ == '__main__':
    unittest.main()
