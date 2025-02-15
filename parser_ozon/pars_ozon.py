import json
import undetected_chromedriver as uc
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys


def page_down(driver, scroll_count=10, pause_time=1):
    for _ in range(scroll_count):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause_time)


def card_info(driver, url_card=''):

	# открывает каждую ссылку в новом окне
	driver.switch_to.new_window('tab')

	driver.implicitly_wait(5)
	driver.get(url=url_card)
	driver.implicitly_wait(5)

	product_id = driver.find_element(
		By.XPATH, '/html/body/div[1]/div/div[1]/div[3]/div[2]/div/div/div/div[2]/button[1]/div'
	).text.split('Артикул: ')[1]

	product_name = driver.find_element(
		By.XPATH, '/html/body/div[1]/div/div[1]/div[3]/div[3]/div[1]/div[1]/div[2]/div/div/div/div[1]/h1').text

	try:
		product_statistic = driver.find_element(
			By.XPATH, '/html/body/div[1]/div/div[1]/div[3]/div[3]/div[1]/div[1]/div[2]/div/div/div/div[2]/div[1]/a/div').text

		if " • " in product_statistic:
			products_star = product_statistic.split(" • ")[0].strip()
			products_reviews = product_statistic.split(" • ")[1].strip()
		else:
			product_statistic = product_statistic

	except:
		product_statistic = None
		products_star = None
		products_reviews = None

	try:
		new_price = driver.find_element(
			By.CSS_SELECTOR,
			'#layoutPage > div.b6 > div.container.c > div.v8k_27.w1k_27.w3k_27 > div.n2m_27 > div > div > '
			'div.v8k_27.w4k_27.w1k_27.k2w_27 > div.l5w_27.wl7_27 > div > div.wl5_27 > div > div > div.lt4_27 > div > '
			'div.lu_27 > div.ul_27 > span.l8t_27.tl8_27.l2u_27').text.strip()
		old_price = driver.find_element(
			By.CSS_SELECTOR,
			'#layoutPage > div.b6 > div.container.c > div.v8k_27.w1k_27.w3k_27 > div.n2m_27 > div > div > '
			'div.v8k_27.w4k_27.w1k_27.k2w_27 > div.l5w_27.wl7_27 > div > div.wl5_27 > div > div > div.lt4_27 > div > '
			'div.lu_27 > div.ul_27 > span.t7l_27.t8l_27.t6l_27.lt8_27').text.strip()

	except:
		new_price = None
		old_price = None

	product_data = (
		{
			'Id Товара': product_id,
			'Название товара': product_name,
			'Цена со скидкой': new_price,
			'Цена без скидки': old_price,
			'Рейтинг товара': products_star,
			'Количество отзывов': products_reviews,
		}
	)

	driver.close()
	driver.switch_to.window(driver.window_handles[0])

	return product_data


def get_links(item_name='умные часы'):
	driver = uc.Chrome()
	driver.implicitly_wait(5)

	driver.get(url='https://ozon.ru/')
	time.sleep(5)

	elem_input = driver.find_element(By.NAME, 'text')
	elem_input.clear()
	elem_input.send_keys(item_name)
	time.sleep(3)

	elem_input.send_keys(Keys.ENTER)
	time.sleep(2)

	url = f"{driver.current_url}&sorting=rating"
	driver.get(url=url)
	time.sleep(2)

	# page_down(driver=driver)

	driver.implicitly_wait(5)
	product_link = 'Ссылки не найдены'
	try:
		links = driver.find_elements(By.CLASS_NAME, 'tile-clickable-element')

		# чтобы убрать дубли ссылок преобразует сначало в сет а потом обратно в список
		product_link = list(set(f'{link.get_attribute('href')}' for link in links))

	except Exception as ex:
		print(f'Ошибка при сборе ссылок {ex}')

	products_link = {}

	for a, b in enumerate(product_link):
		products_link.update({a: b})

	with open('products_link.json', 'w', encoding='utf-8') as file:
		json.dump(products_link, file, indent=4, ensure_ascii=False)

	time.sleep(2)

	products_data = []

	for url_card in product_link:
		data = card_info(driver=driver, url_card=url_card)
		print(f'Собрал данные с товара {data.get('Id Товара')}')
		time.sleep(2)
		products_data.append(data)

	with open('PRODUCT_INFO.json', 'w', encoding='utf-8') as file:
		json.dump(products_data, file, indent=4, ensure_ascii=False)

	driver.close()
	driver.quit()


def main():
	get_links()


if __name__ == '__main__':
	main()