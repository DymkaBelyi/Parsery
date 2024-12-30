import json
import undetected_chromedriver as uc  # библиотека чтобы не смогли обнаружить парсер
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


class SafeChrome(uc.Chrome):
	def __del__(self):
		try:
			if self.service.process:
				self.quit()
		except Exception:
			pass


class Avito_pars():  #items это список всех критериев которые по которым мы хотим искать
	def __init__(self, url: str, items: list, count: int = 20, version_main = None):
		self.url = url
		self.items = items
		self.count = count
		self.version_main = version_main
		self.data = []

	# в этом методе будем запускать сам браузер
	def __set_up(self):
		options = Options()
		options.add_argument('--headless')  # Браузер запускается, но окно не вылазит
		self.driver = SafeChrome(version_main=self.version_main, options=options)

	# в этом методе переходим по заданной ссылке
	def __get_url(self):
		self.driver.get(self.url)

	# метод,который будет сам переходить по страничкам и собирать данные
	def __paginator(
			self
	):  # пользователь передает число страниц, которые нужно спарсить и если оно равно нулю то цикл заканчивается
		while self.driver.find_elements(By.CSS_SELECTOR, "[data-marker='pagination-button/nextPage']") and self.count > 0:
			self.__parse_page()
			next_page = self.driver.find_element(By.CSS_SELECTOR, "[data-marker='pagination-button/nextPage']")
			self.driver.execute_script("arguments[0].scrollIntoView(true);", next_page)
			next_page.click()
			self.count -= 1

	# метод, который будет собирать данные на одной страничке
	def __parse_page(self):
		titles = self.driver.find_elements(By.CSS_SELECTOR, "[data-marker='item']")
		for title in titles:
			try:
				name = title.find_element(By.CSS_SELECTOR, "[itemprop='name']").text
				description = title.find_element(By.CSS_SELECTOR, "[itemprop='description']").get_attribute(
					'content'
				)
				link = title.find_element(By.CSS_SELECTOR, "[data-marker='item-title']").get_attribute('href')
				price = title.find_element(By.CSS_SELECTOR, "[itemprop='price']").get_attribute('content')
				data = {
					'Название': name,
					'Описание': description,
					'Ссылка': link,
					'Цена': price,
				}
				# Пишем проверку если слова, которые пользователь ввел есть в описании и цена ровна 0, то добавляем
				if any([item.lower() in description.lower() for item in self.items]) and int(price) > 45000:
					self.data.append(data)
					print(data)
			except Exception as e:
				print(f"Ошибка при обработке элемента: {e}")

		self.__save_data()

	def __save_data(self):
		with open("items.json", 'w', encoding='utf-8') as f:
			json.dump(self.data, f, ensure_ascii=False, indent=4)

	def parse(self):
		self.__set_up()
		self.__get_url()
		self.__paginator()


if __name__ == "__main__":
	Avito_pars(
		url='https://www.avito.ru/moskovskaya_oblast/zapchasti_i_aksessuary/shiny_diski_i_kolesa/shiny-ASgBAgICAkQKJooLgJ0B',
		count=5,
		version_main=131,
		items=["шины"]  #Ключевые слова для поиска
	).parse()
