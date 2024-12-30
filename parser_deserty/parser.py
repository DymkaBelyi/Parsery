import re
import time
import pandas as pd
import undetected_chromedriver as uc  # библиотека чтобы не смогли обнаружить парсер
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager  # пакет для автоматической установки драйвера


class SafeChrome(uc.Chrome):
	def __del__(self):
		try:
			if self.service.process:
				self.quit()
		except Exception:
			pass


def get_products():
	options = Options()
	# options.add_argument('--headless')
	options.add_argument(
		'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
		)
	driver = SafeChrome(
		driver_executable_path='C:/Users/Belov/chromedriver/chromedriver-win64/chromedriver.exe', options=options
		)
	page = 1
	all_links = []
	while True:
		url = f'https://flowwow.com/moscow/wedding-cakes/page-{page}/'
		driver.get(url)
		driver.implicitly_wait(5)
		products = driver.find_elements(By.CSS_SELECTOR, "[class='tab-content-products-item']")
		for product in products:
			links = product.find_element(By.CSS_SELECTOR, "[class='product-card ']").get_attribute('href')
			all_links.append(links)
		print(page)
		driver.implicitly_wait(5)
		page += 1
		if page == 3:
			break

	driver.quit()
	return all_links


def scrape_product_data(driver, url):
	data = {}
	try:
		driver.get(url)
		driver.implicitly_wait(5)
		data["Категория"] = 'Торты'
		data["URL"] = url
		driver.implicitly_wait(5)
		try:
			foto = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div[3]/div/div[1]/div[1]/div/img").get_attribute('src')
			data["Ссылка на фото"] = foto
		except Exception:
			foto = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[1]/div[1]/div[1]/div/div/div[2]/div/div[3]/div/div[1]/div[2]/div/img").get_attribute('src')
			data["Ссылка на фото"] = foto
		data["Название"] = driver.find_element(By.CSS_SELECTOR, "h1[data-v-1231df28]").text
		data["Цена"] = driver.find_element(By.CSS_SELECTOR, "span[data-v-32ae3f6f]").text.replace('\n', ' ')
		data["Вес товара"] = driver.find_element(By.XPATH, "//h3[@class='property-name' and contains(text(), 'Вес товара')]/following-sibling::*[1]").text
		res = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[1]/div[2]/div[4]/ul/li[2]/div/span").text
		res_int = "".join(re.findall(r"\d", res))
		data["Добавили в подборки"] = res_int[:3]
		data["Магазин"] = driver.find_element(By.CSS_SELECTOR, "[class='shop-name']").text
		data["Ссылка на магазин"] = driver.find_element(By.CSS_SELECTOR, "[class='shop-link']").get_attribute('href')
		ocenka = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[3]/div/div[3]/div[1]/p/span").text
		data["Рейтинг магазина"] = ocenka[:4]
		try:
			grade = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[3]/div/div[3]/div[2]/p/span[1]").text
			grade_int = "".join(re.findall(r"\d", grade))
			data["Оценок"] = grade_int
		except Exception:
			grade_int = ' '
			data["Оценок"] = grade_int
		try:
			purchase = driver.find_element(By.XPATH, "/html/body/div[1]/div/div/section/div[1]/div/div[2]/div/div[3]/div/div[3]/div[2]/p/span[3]").text
			purchase_int = "".join(re.findall(r"\d", purchase))
			data["Покупок"] = purchase_int
		except Exception:
			purchase_int = ' '
			data["Покупок"] = purchase_int
		print(data)

	except Exception as e:
		print(f"Ошибка при обработке {url}: {e}")
	return data



def main():
	options = Options()
	# options.add_argument('--headless')
	options.add_argument(
		'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
		)
	driver = SafeChrome(
		driver_executable_path='C:/Users/Belov/chromedriver/chromedriver-win64/chromedriver.exe', options=options
		)
	all_data = []

	try:
		for url in get_products():
			print(f"Обработка {url}")
			product_data = scrape_product_data(driver, url)
			if product_data:
				all_data.append(product_data)
				driver.implicitly_wait(2)
		print(all_data)
		if all_data:
			df = pd.DataFrame(all_data)
			df.to_excel("products.xlsx", index=False)
			print("Данные успешно сохранены в файл 'products.xlsx'")
	finally:
		driver.quit()


if __name__ == "__main__":
	start_time = time.time()
	main()
	print(f"Время выполнения: {time.time() - start_time:.2f} секунд")
