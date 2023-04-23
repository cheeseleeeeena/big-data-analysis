from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time, codecs
from bs4 import BeautifulSoup



options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')

driver = webdriver.Chrome(service=Service(r'./chromedriver/chromedriver.exe'),
                          options=options)

page = driver.get("https://womany.net/interests/sense/susanmiller")

time.sleep(5)

try:
    for i in range(5):
        more_button = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//*[@id='interest-topic']/div[1]/div/div/button"))
    )
        more_button.click()
        print("load more button clicked!")
        time.sleep(2)

    # soup = BeautifulSoup(driver.page_source, 'lxml')

    file = codecs.open("my_page.html", "w", "utf-8")
    file.write(driver.page_source)
    file.close()

    print("html file saved!")

finally:
    driver.quit()