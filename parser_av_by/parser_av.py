import requests
import json
from bs4 import BeautifulSoup
import time, random
# import sqlite_client



def get_cars():

    HEADERS = {
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }
    URL = "https://cars.av.by/filter?brands[0][brand]=989&brands[0][model]=1927&brands[0][generation]=10119"

    dict_cars = {}
    count = 1
    while True:
        if count > 1:
            url = URL + '&page=' + str(count)
        else:
            url = URL

        r = requests.get(url=url, headers=HEADERS)
        soup = BeautifulSoup(r.text, "html.parser")

        if count == 1:
            pagination = soup.find('div', class_="paging__button").find_all('div', class_="listing-item")

        article_cars = soup.find_all('div', class_="listing-item")

        for article_car in article_cars:
            article_title = article_car.find('span', class_="link-text").text.strip()
            article_url = f"https://cars.av.by{article_car.find('a', class_="listing-item__link").get("href")}"
            article_price = article_car.find('div', class_="listing-item__priceusd").text.strip()
            article_params = article_car.find('div', class_="listing-item__params").text.strip()
            article_location = article_car.find('div', class_="listing-item__location").text.strip()
            article_date = article_car.find('div', class_="listing-item__date").text.strip()
            try:
                article_information = article_car.find('div', class_="listing-item__message").text.strip()
            except:
                article_information = 'Информация отсутствует'

            article_id = article_url.split("/")[-1]
            article_id = article_id[:-4]

            print(f"Название авто: {article_title}\nЦена авто: {article_price}\nПараметры авто: {article_params}\n"
                  f"Ссылка на авто: {article_url}\nГород в котором продается: {article_location}\n"
                  f"Дата подачи обьявления: {article_date}\nИнформация об авто: {article_information}\n\n")

            dict_cars[article_id] = {
                'Название авто': article_title,
                'Цена авто': article_price,
                'Параметры авто': article_params,
                'Город продажи': article_location,
                'Дата подачи обьявления': article_date,
                'Ссылка на авто': article_url,
                'Информация от авто': article_information,
            }

        with open("../cars_peugeot.json", "w", encoding="utf-8") as file:
            json.dump(dict_cars, file, indent=7, ensure_ascii=False)


        print(count)
        time.sleep(random.choice([3, 5, 7]))
        if count == pagination:
            break
        elif count == 13:
            break
        count += 1



def main():
    get_cars()



if __name__ == "__main__":
    main()


