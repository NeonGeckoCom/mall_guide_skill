import urllib.request as urllib2
import requests
from bs4 import BeautifulSoup
from neon_utils.skills.neon_skill import LOG


class RequestHandler:

    def __init__(self):
        self.found_shops = []

    def existing_lang_check(self, user_lang, url):
        link = url+user_lang+'/directory/'
        response = requests.get(link)
        if response.status_code == 200:
            LOG.info('This language is supported')
            return True
        else:
            LOG.info('This language is not supported')
            return False

    def get_shop_data(self, url, user_request):
        page = urllib2.urlopen(url)
        soup = BeautifulSoup(page, 'html.parser')

        for shop in soup.find_all(attrs={"class": "directory-tenant-card"}):
            info = shop.find_next(attrs={"class": "tenant-info-container"})
            name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
            if name.lower() in user_request.lower():
                logo = shop.find_next("img").get('src')
                hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
                location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
                shop_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
                self.found_shops.append((shop_data))
                LOG.info(f"{name} {hours} {location} {logo}")
            else:
                LOG.info('NOTHING FOUND')
        return self.found_shops

    def image_extraction(self):
        # Todo extract image from web-pade
        ...
