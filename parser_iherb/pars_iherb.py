import undetected_chromedriver as uc
import time, random
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd


def pars_product():
    options = Options()
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/132.0.6834.84 Safari/537.36'
    )
    driver = uc.Chrome(options=options)
    page = 1

    all_links = []
    while True:
        url = f'https://kg.iherb.com/c/california-gold-nutrition?p={page}'
        driver.get(url)
        driver.implicitly_wait(5)
        links = driver.find_elements(By.CLASS_NAME, 'product-link')
        for link in links:
            lin = link.get_attribute('href')
            all_links.append(lin)
        print(page)

        page += 1
        time.sleep(random.choice([3, 5, 7]))
        if page == 10:
            break

    driver.quit()
    print(len(all_links))
    return all_links


def get_info_product(url):
    options = Options()
    options.add_argument(
        'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/132.0.6834.84 Safari/537.36'
    )

    driver = uc.Chrome(options=options)

    data = {}

    try:
        driver.get(url)
        time.sleep(11)

        data['Название'] = driver.find_element(
            By.XPATH, '/html/body/div[8]/article/div[1]/div[2]/section/div/section[1]''/div/h1').text
        data['Ссылка'] = url
        data['Код товара'] = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
            By.XPATH, "(//ul[@id='product-specs-list']/li/span)[3]"))
        ).text
        try:
            data['Цена'] = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
                By.XPATH, "/html/body/div[8]/article/div[1]/div[2]/section/section[2]/div[1]/div/div/div/label[1]"
                          "/section/section[1]/div[5]/section/div/div[2]/div/b"))
            ).text
        except:
            data['Цена'] = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
				By.XPATH, "(//div[@class='price-inner-text'])[1]"))).text
        data['Есть ли в наличии'] = driver.find_element(
            By.XPATH, '/html/body/div[8]/article/div[1]/div[2]/section/div/section[2]/div/div/div[1]/strong').text
        goden_do = driver.find_element(By.XPATH, '/html/body/div[8]/article/div[1]/div[2]/section/div/div[2]/section[1]/ul/li[2]').text
        if ": " in goden_do:
            goden = goden_do.split(": ")[0].strip()
            data['Срок годности'] = goden_do.split(": ")[1].strip()
        data['UPC'] = WebDriverWait(driver, 15).until(EC.presence_of_element_located((
            By.XPATH, "(//ul[@id='product-specs-list']/li/span)[4]"))
        ).text
    except Exception as ex:
        print(f"Ошибка при обработке {url}: {ex}")
    finally:
        driver.quit()

    print(data)
    return data


def save_to_excel(data_list, file_name='product_info.xlsx'):
    # Создаем DataFrame из списка данных
    df = pd.DataFrame(data_list)

    df.to_excel(file_name, index=False, engine='openpyxl')
    print(f'Все данные сохраненны в файл {file_name}')


def main():
    product_links = pars_product()
    all_product_data = []
    for link in product_links:
        product_info = get_info_product(link)
        if product_info:
            all_product_data.append(product_info)

    save_to_excel(all_product_data)


if __name__ == "__main__":
    main()

