from bs4 import BeautifulSoup #Библиотека для скрапинга
from selenium import webdriver #эмулятор браузера
from selenium.webdriver.chrome.options import Options #для того, чтобы сделать браузер безголовым
import json, io #для вывода информации в json файл
from datetime import datetime #для создания уникального имени файла .json
from selenium.webdriver.common.by import By  #Для поиска элементов
import time
from urllib.request import urlopen


def get_download(url_article):
    html_article = urlopen(url_article)
    page_article = BeautifulSoup(html_article.read(), 'html.parser')
    #print(page_article)
    a_list = page_article.find_all('meta', {'name': 'citation_pdf_url'})
    if len(a_list) == 1:
        return str(a_list).split('"')[1]
    else:
        return "Nothing"


def get_html(driver):
    time.sleep(2)
    source_data = driver.page_source
    soup = BeautifulSoup(source_data, 'html.parser')
    return soup


def get_filter_year(driver, tag_content, years):
    try:
        tag_list_str = []
        for i in tag_content:
            tag_list_str.append(i.find('span').get_text())
        if years is None:
            return driver
        input_elements = driver.find_elements_by_css_selector('.tag-list input')
        input_elements[0].send_keys(years[0])
        input_elements[1].send_keys(years[1])
        button = driver.find_element(By.XPATH, '//span[text()="Задать"]')
        button.click()
        return driver
    except Exception:
        print("При выборе журнала произошла ошибка: " + str(Exception))
        return driver


def get_filter_theme(driver, tag_content):
    try:
        tag_list_str = []
        for i in tag_content:
            tag_list_str.append(i.find('span').get_text())
        print("Выберите или укажите -1")
        for i in range(0, len(tag_list_str)): print(str(i) + ". " + tag_list_str[i])
        value = int(input())
        if value == -1:
            print("Вы пропустили выбор.")
            return
        button = driver.find_element(By.XPATH, '//span[text()="' + tag_list_str[value] + '"]')
        button.click()
        return driver
    except:
        print("При выборе произошла ошибка")
        return driver


def get_count(html_articles_search, def_end=False, def_end_value=0): #Получить количество страниц
    # Если нужно ограничить максимально возможное число страниц, то указываем def_end = True и записываем max в def_end_value
    try:
        pageListHTML = html_articles_search.find('ul', {'class': 'paginator'}).find_all('a')
        count = int(pageListHTML[len(pageListHTML) - 1].get_text())
        if count >= def_end_value and def_end:
            count = def_end_value
        print("Количество найденных страниц: " + str(count))
        return count
    except:
        print("Exception count")
        return 0


def get_page(driver, c):
    try:
        content = driver.find_element_by_class_name("paginator")
        button = content.find_element(By.XPATH, '//a[text()="' + str(c) + '"]').click()
    except:
        return


def get_content(path, url, years, def_end=False, def_end_value=1):
    driver = None
    try:
        options = Options()
        options.headless = True
        driver = webdriver.Chrome(executable_path=path, options=options)
        driver.get(url)

        generated_html = driver.page_source
        html_articles_search = BeautifulSoup(generated_html, 'html.parser')
        tag_content = html_articles_search.find_all('ul', {'class': 'tag-list'})

        get_filter_year(driver, tag_content[0].find_all('li'), years)    #Заполнение фильтра по годам
        get_filter_theme(driver, tag_content[1].find_all('li'))          #Заполнение фильтра по темам
        get_filter_theme(driver, tag_content[2].find_all('li'))          #Заполнение фильтра по типу статей
        html_result = get_html(driver)

        count = get_count(html_result, def_end, def_end_value)
    except:
        count = 0
    result = []
    if count != 0:
        for j in range(1, count+1):
            try:
                html_result = get_html(driver)
                articlesList = html_result.find('ul', {'id': 'search-results'})
                a_list = articlesList.find_all('li')

                for i in a_list:
                    url_article = "https://cyberleninka.ru" + str(i.find('h2', {'class': 'title'}).find('a')).split('"')[1]
                    result.append({"name": i.find('h2', {'class': 'title'}).get_text(),
                                   "author": i.find('span').get_text(),
                                   "magazine": i.find('span', {'class': 'span-block'}).get_text(),
                                   "url": url_article,
                                   "download": get_download(url_article)
                                   })
                print("Страница №" + str(j) + ": Пройдено!")
            except:
               print("Страница №" + str(j) + ": Ошибка!")
               continue
            finally:
               get_page(driver, j+1)
    driver.quit()
    return result


def save_result(content):
    try:
        #datetime_string = datetime.now().strftime('%m.%d.%y %H-%M-%S')

        with io.open("temp.json", 'w', encoding='utf-8') as f:  # Выводим результат в Json файл
            json.dump(content, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False


class Parsing:
    def_end = False #Ограничить количество найденных страниц?
    def_end_value = 1 #Если да(True), то до какой страницы осуществляем поиск?
    year = [2017, 2021] #None или [2021, 2021] или [2020, 2021] указываем либо год, либо диапазон от и до

    def create_request(self, in_request):
        #path = r'C:\\Users\\AlexWells\\Desktop\\CyberLeninkaParser\\Chromedriver'  # Путь до Chromedriver.exe
        path = "Chromedriver"
        url = "https://cyberleninka.ru/search?q=" + str(in_request)  # Ссылка с запросом
        def_end = self.def_end
        def_end_value = self.def_end_value
        year = self.year

        print("Запускаем скрапинг сайта, ожидайте...")
        content = get_content(path, url, year, def_end, def_end_value)  # Получаем статьи со всех страниц

        return content


#el = Parsing()
#res = el.create_request("блокчейн")
# print(res)