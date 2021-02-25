from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time
import random
import logging


#from pyvirtualdisplay import Display
#display = Display(visible=0, size=(1280, 1024))
#display.start()

driver = webdriver.Firefox()
driver.maximize_window()
#driver.get("https://solotony.com/")
res = driver.get("https://www.rigla.ru/product/100118")
print(res)
element = driver.find_element_by_tag_name('body')
print(element)
print(element.text)
