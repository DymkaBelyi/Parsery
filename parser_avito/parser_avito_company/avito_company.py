import time
import re

import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from concurrent.futures import ThreadPoolExecutor, as_completed

from webdriver_manager.chrome import ChromeDriverManager


class SafeChrome(uc.Chrome):
    def __del__(self):
        try:
            if self.service.process:
                self.quit()
        except Exception:
            pass


# Функция загрузки ссылок из файла
def load_links_from_file(filename="links.txt"):
    with open(filename, "r", encoding="utf-8") as file:
        return [line.strip() for line in file if line.strip()]


def info_company(url):
    options = Options()
    # options.add_argument("--headless=new")  # Запуск без интерфейса
    options.add_argument("--disable-blink-features=AutomationControlled")  # Скрываем автоматизацию
    options.add_argument("--start-maximized")
    options.add_argument("--disable-infobars")
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/134.0.6998.89 Safari/537.36'
    )
    driver = SafeChrome(executable_path=ChromeDriverManager().install(),
                        options=options)
    driver.get(url)
    driver.implicitly_wait(5)

    try:
        # Название компании
        try:
            name_company = driver.find_element(By.XPATH, "//h1").text.strip()
        except NoSuchElementException:
            name_company = ""

        # Рейтинг компании
        try:
            rating_company = driver.find_element(By.CSS_SELECTOR, "[data-marker='profile/score']").text.strip()
        except NoSuchElementException:
            rating_company = ""

        # Количество активных объявлений
        try:
            active_advertisements = driver.find_element(
                By.CSS_SELECTOR, "[data-marker='extended_profile_tabs/tab(active)']").text.strip()
            active_advertisements = re.sub(r'\D', '', active_advertisements)
        except NoSuchElementException:
            active_advertisements = ""

        try:
            completed_advertisements = driver.find_element(
                By.CSS_SELECTOR, "[data-marker='extended_profile_tabs/tab(closed)']").text.strip()
            completed_advertisements = re.sub(r'\D', '', completed_advertisements)
        except:
            completed_advertisements = ""

        # На Avito с (дата регистрации)
        try:
            on_avito = driver.find_element(By.CSS_SELECTOR, "[data-marker='registered']").text.strip()
            on_avito = on_avito.replace("На Авито ", "")  # Убираем лишний текст
        except NoSuchElementException:
            on_avito = ""

        # Количество отзывов
        try:
            reviews = driver.find_element(By.CSS_SELECTOR, "[data-marker='profile/summary']").text.strip()
            reviews = re.sub(r'\D', '', reviews)
        except NoSuchElementException:
            reviews = ""

        data = {
            "Компания": name_company,
            "Ссылка": url,
            "Активные объявления": active_advertisements,
            "Завершенные": completed_advertisements,
            "На Авито": on_avito,
            "Оценка": rating_company,
            "Количество отзывов": reviews,
            "Квартиры": [],
            "Отзывы": [],
            "Даты": []
        }

        #ПРОКРУТКА СТРАНИЦЫ, ЧТОБЫ ЗАГРУЗИТЬ ВСЕ ОТЗЫВЫ
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)  # Ждем, пока подгрузятся новые отзывы

            try:
                show_more_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "[data-marker='rating-list/moreReviewsButton']"))
                )
                driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)
            except (NoSuchElementException, TimeoutException):
                break  # Выходим из цикла, если кнопки нет

        #ПРОВЕРЯЕМ, ЕСТЬ ЛИ ОТЗЫВЫ
        time.sleep(2)
        reviews_elements = driver.find_elements(By.CLASS_NAME, "style-snippet-BzYXq")

        if not reviews_elements:
            # print("❌ Ошибка: отзывы не найдены. Возможно, изменился селектор.")
            pass


        #ИЗВЛЕКАЕМ ДАННЫЕ ИЗ ОТЗЫВОВ
        for element in reviews_elements:
            try:
                date = element.find_element(By.CSS_SELECTOR, "header div:nth-child(2) div:nth-child(2) p").text.strip()
                apartments = element.find_element(By.CSS_SELECTOR, "div:nth-child(1) div p span").text.strip()

                try:
                    review_text = element.find_element(By.CSS_SELECTOR,
                                                       "p.stylesMarningNormal-module-paragraph-m-pH9s3").text.strip()
                except NoSuchElementException:
                    review_text = "Отзыв отсутствует"

                data["Квартиры"].append(apartments)
                data["Отзывы"].append(review_text)
                data["Даты"].append(date)
            except (NoSuchElementException, TimeoutException):
                # print("Ошибка: один из элементов отзыва не найден.")
                pass

        return data

    except Exception as e:
        print("❌ Ошибка:", e)
        return None

    finally:
        driver.quit()  # Закрываем браузер
        del driver


def save_to_excel(data, filename="output.xlsx"):
    rows = []

    for entry in data:
        base_info = [
            entry["Компания"],
            entry["Ссылка"],
            entry["Активные объявления"],
            entry["Завершенные"],
            entry["На Авито"],
            entry["Оценка"],
            entry["Количество отзывов"]
        ]

        # Добавляем строки с квартирами и отзывами
        for i, (apartment, review, date) in enumerate(zip(entry["Квартиры"], entry["Отзывы"], entry["Даты"])):
            if i == 0:
                # Добавляем полную информацию только в первой строке
                rows.append(base_info + [apartment, review, date])
            else:
                # В остальных строках оставляем повторяющиеся данные пустыми
                rows.append([""] * len(base_info) + [apartment, review, date])

    df = pd.DataFrame(rows, columns=[
        "Компания", "Ссылка", "Активные объявления", "Завершенные", "На Авито", "Оценка",
        "Количество отзывов", "Квартира", "Отзыв", "Дата"
    ])

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="Sheet1", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Sheet1"]

        # Запись заголовков
        header_format = workbook.add_format({"bold": True, "align": "center", "valign": "vcenter", "border": 1})
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num, value, header_format)


def main():
    links = load_links_from_file("links.txt")
    all_data = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_url = {executor.submit(info_company, url): url for url in links}

        for future in as_completed(future_to_url):
            try:
                result = future.result()
                if result:
                    all_data.append(result)
            except Exception as e:
                print(f"❌ Ошибка в потоке: {e}")

    if all_data:
        save_to_excel(all_data, "info_company.xlsx")
        print("✅ Файл info_company.xlsx сохранен успешно.")
    else:
        print("❌ Нет данных для сохранения.")


if __name__ == "__main__":
    main()
