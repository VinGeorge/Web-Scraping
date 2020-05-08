import sys
import re
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup as bs
from selenium.webdriver.common.keys import Keys



class Collection:
    def __init__(self, url):

        self.url = url
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("start-maximized")
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.chrome_options.add_experimental_option("prefs", prefs)

    def scroller(self, wine_list, wine_ratings):

        driver = webdriver.Chrome(options=self.chrome_options)
        driver.get(self.url)

        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                    "//div[starts-with(@class, 'responsiveDropdownMenu__title--')]//following::span[starts-with(@class, 'responsiveDropdownMenu__label--')]"))).click()
        WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.XPATH,
                                                                    "//div[starts-with(@class, 'responsiveDropdownMenu__menu--')]//a[@id='desc__ratings_count']"))).click()

        pages = []
        try:
            for element in wine_list:
                driver.find_element_by_xpath(
                    "//span[@class='pill__text--24qI1' and text()='{}']".format(element)).click()
                for mark in wine_ratings:
                    driver.find_element_by_xpath("//input[@id='{}']".format(mark)).click()
                    time.sleep(2)
                    lenOfPage = driver.execute_script(
                        "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                    match = False
                    while match is False:
                        lastCount = lenOfPage
                        time.sleep(3)
                        lenOfPage = driver.execute_script(
                            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                        if lastCount == lenOfPage:
                            driver.find_element_by_tag_name('body').send_keys(Keys.CONTROL + Keys.HOME)
                            time.sleep(3)
                            lenOfPage = driver.execute_script(
                                "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
                            if lastCount == lenOfPage:
                                match = True

                    # Now that the page is fully scrolled, lets grab the source code
                    source_data = driver.page_source

                    # Put scrolled page in source into BeautifulSoup and append to the collection
                    soup = bs(source_data)
                    pages.append(soup)

                    driver.find_element_by_xpath(
                        "//span[@class='pill__text--24qI1' and text()='{}']".format(element)).click()

                time.sleep(3)

        finally:
            driver.quit()

        return pages

    @staticmethod
    def processing(pages):
        urls = []
        for page in pages:
            last_argument = len(page.find_all(class_="anchor__anchor--2QZvA", href=True, target=True))

            for i in range(0, (last_argument - 5)):
                wine = page.find_all(class_="anchor__anchor--2QZvA", href=True, target=True)[i]['href']
                urls.append('https://www.vivino.com{}'.format(wine))

        return urls


class Chief:
    def __init__(self, url=None):
        self.url = url
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("start-maximized")
        prefs = {"profile.managed_default_content_settings.images": 2}
        self.chrome_options.add_experimental_option("prefs", prefs)

    def soup_maker(self):
        driver = webdriver.Chrome(options=self.chrome_options)
        driver.get(self.url)
        soup = bs(driver.page_source, features= 'html.parser')
        driver.quit()

        return soup


class PageScraper:
    def __init__(self, soup=None):

        self.soup = soup

    def avalible_wine_types(self):

        finder = self.soup.find_all(class_="filterByWineType__items--2GBgf")

        return [re.findall('[A-Z][^A-Z]*', tag.text) for tag in finder][0]

    def avalible_rating_scores(self):

        finder = self.soup.find_all(class_="radio__radioBtn--2nKnw")

        return [tag['id'] for tag in finder]

    def unified_scraper(self, class_name=None, href=None, image=None, class_start=None):

        if href is True:
            summary = self.soup.find_all(class_=class_name, href=True)
            return summary
        elif image is True:
            image = self.soup.select("div[class^={}]".format(class_start))
            return image
        else:
            element = self.soup.find_all(class_=class_name)
            return [tag.text for tag in element]

def parser(soup, url=None):

    elements = PageScraper(soup=soup)
    properties = {}

    try:

        summary = elements.unified_scraper(class_name="anchor__anchor--2QZvA wineSummary__link--zVpWl", href=True)
        name = elements.unified_scraper(class_name="winePageHeader__vintage--2Vux3")[0]
        rating = elements.unified_scraper(class_name="vivinoRating__rating--4Oti3")[0]
        ratings_count = elements.unified_scraper(class_name="vivinoRating__ratingCount--NmiVg")[0]
        sort_string = elements.unified_scraper(class_name='wineLocationHeader__text--3irYN')
        sort = re.findall('[a-zA-Z]* wine', str(sort_string))[0]
        country = elements.unified_scraper(class_name='anchor__anchor--3DOSm')[0]
        price_string = elements.unified_scraper(class_name = 'purchaseAvailabilityPPC__notSoldContent--1yZZ0')

        image = elements.unified_scraper(class_start='basicWineDetailsHeader__basicWineDetailsHeader--19I9v', image=True)

        price = re.findall('\d*₽', str(price_string))[0]

        properties['rating'] = rating
        properties['rating_cout'] = re.split(pattern=" ", string=ratings_count)[0]
        properties['country'] = country
        properties['sort'] = sort
        properties['price'] = re.split(pattern='₽', string=price)[0]
        properties['image'] = 'https://{}'.format(re.findall('images\S*"', str(image))[0])[:-1]
        properties['url'] = url

        winery = []
        grapes = []
        food_pairing = []
        styles = []
        regions = []
        something_new = []

        for tag in summary:

            if 'wineries' in tag['href']:
                winery.append(tag.text)
                properties['winery'] = winery

            elif 'grapes' in tag['href']:
                grapes.append(tag.text)
                properties['grapes'] = grapes

            elif 'wine-regions' in tag['href']:
                regions.append(tag.text)
                properties['wine-regions'] = regions

            elif 'wine-styles' in tag['href']:
                styles.append(tag.text)
                properties['styles'] = styles

            elif 'food-pairing' in tag['href']:
                food_pairing.append(tag.text)
                properties['food-pairing'] = food_pairing

            else:
                something_new.append(tag.text)
                properties['something_new'] = something_new
    except:

        error = sys.exc_info()[0]
        print("Error occurred: {} in url {}".format(error))

    finally:
        None

    return {name: properties}

def harvest(urls, path_and_name, time_sleep=None):
    wines = {}
    all_urls = len(urls)

    for i, url in enumerate(urls):

        try:

            soup = Chief(url[0])
            soup = soup.soup_maker()
            data = parser(soup, url)
            wines.update(data)

            time.sleep(time_sleep)

            if i % 100 == 0:
                print("Downloaded {}/{} pages, please wait".format(i, all_urls))
                backup = pd.DataFrame(wines).transpose()
                backup.to_csv(path_or_buf='{}_(backup-{}).csv'.format(path_and_name, i), header=True)

        except Exception as e:

            print("Warning, error ocurred: {} in url {}".format(e, url))

    wine_data = pd.DataFrame(wines).transpose()
    wine_data.to_csv(path_or_buf='{}.csv'.format(path_and_name), header=True)

    return print('Finish')