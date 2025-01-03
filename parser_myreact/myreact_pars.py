import requests
from bs4 import BeautifulSoup
import time, random
import json
import re

def get_mens_shoes():
    URL = "https://myreact.ru/muzhskaya-obuv/?per_page=108"
    HEADERS = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }

    dict_mens_shoes = {}
    count = 1
    while True:
        if count > 1:
            url = f"https://myreact.ru/muzhskaya-obuv/page/{count}/?per_page=108"
        else:
            url = URL

        response = requests.get(url=url, headers=HEADERS)
        soup = BeautifulSoup(response.text, 'html.parser')
        for links in soup.find_all('span', class_='wd-entities-title'):
            link = links.findNext('a').get('href')
            shoe_link = link
            r = requests.get(shoe_link)
            soups = BeautifulSoup(r.text, 'html.parser')
            try:
                shoe_title = soups.find('h1', class_='product_title entry-title').text.strip()
            except:
                shoe_title = 'Мужские кросовки'
            try:
                shoe_price = soups.find('p', class_='price single-big-price').text.replace('Цена:', '').strip()
            except:
                shoe_price = 'Цена отсутствует'
            try:
                shoe_store = soups.find('a', rel='tag').text.strip()
            except:
                shoe_store = ' '
            try:
                shoe_description = soups.find('div', class_='wpb_wrapper').find('p').text.strip()
                if shoe_description == 'Или позвоните':
                    shoe_description = soups.find('div', id='tab-description').text.strip()
                else:
                    shoe_description = soups.find('div', class_='wpb_wrapper').find('p').text.strip()
            except:
                shoe_description = 'Описание отсутствует'
            shoe_article = soups.find('span', class_='meta-label').text.strip()
            shoe_type = 'normal'
            try:
                shoe_category = soups.find_all(class_='meta-line')[6].text.replace('Категория:', '').strip()
            except:
                shoe_category = ' '

            shoe_gender = soups.find(string=re.compile('Женский, Мужской'))
            if shoe_gender == None:
                shoe_gender = 'Женский, Мужской'
            else:
                shoe_gender = soups.find(string=re.compile('Женский, Мужской'))
            shoe_local = 'rus'
            price_old = 'Отсутсвует'

            shoe_id = shoe_article
            dict_mens_shoes[shoe_id] = {
                    'title': shoe_title,
                    'store': shoe_store,
                    'link': shoe_link,
                    'price': shoe_price,
                    'price0ld': price_old,
                    'type': shoe_type,
                    'gender': shoe_gender,
                    'description': shoe_description,
                    'category': shoe_category,
                    'locale': shoe_local,
                }

        with open("mens_shoes.json", "w", encoding="utf-8") as file:
            json.dump(dict_mens_shoes, file, indent=7, ensure_ascii=False)

        print(count)
        time.sleep(random.choice([1, 3, 5]))
        if count == 44:
            break
        count += 1


def main():
    get_mens_shoes()


if __name__ == "__main__":
    main()
