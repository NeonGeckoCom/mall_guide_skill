from urllib.error import HTTPError
import requests
import bs4
from neon_utils.skills.neon_skill import LOG
import urllib
import urllib.request

class RequestHandler():

    def __init__(self) -> None:
        pass

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
      

    def get_shop_data(self, url, user_request):
        found_shops = []
        soup = self.parse(url)
        for shop in soup.find_all(attrs={"class": "directory-tenant-card"}):
            logo = shop.find_next("img").get('src')
            info = shop.find_next(attrs={"class": "tenant-info-container"})
            name = info.find_next(attrs={"class": "tenant-info-row"}).text.strip().strip('\n')
            if name.lower() in user_request.lower():
                hours = info.find_next(attrs={"class": "tenant-hours-container"}).text.strip('\n')
                location = info.find_next(attrs={"tenant-location-container"}).text.strip('\n')
                shop_data = {'name': name, 'hours': hours, 'location': location, 'logo': logo}
                found_shops.append(shop_data)
        return found_shops

    # def image_extraction():
    #     # Todo extract image from web-pade
    #     ...
