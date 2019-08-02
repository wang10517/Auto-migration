from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from similarity.jarowinkler import JaroWinkler
from similarity.cosine import Cosine
from similarity.longest_common_subsequence import LongestCommonSubsequence
import pandas as pd
import re
import unittest
import time
import re
import openpyxl
import csv
import xpath_config


def importSiteStream(pathToSites, sheetName):
    workbook = openpyxl.load_workbook(pathToSites)
    worksheet = workbook[sheetName]
    return worksheet


def getSites(sheet):
    urls = []
    # index here to be changed to sheet-specific
    for row in sheet.iter_rows(min_row=2, min_col=6, max_col=6):
        for url in row:
            urls.append(url.hyperlink.display)
    domain_name = sheet['B']
    domain_name = domain_name[1:]

    return urls, domain_name


def handleLogin(driver):
    # do something on the login page// enter the login information
    email_input = driver.find_element_by_id('email')
    email_input.send_keys('swang@orisintel.com')
    password_input = driver.find_element_by_id('password')
    password_input.send_keys('990622$Yimod')
    driver.find_element_by_id('login').click()
    return driver


def getEndInfo(xpathToId, xpathToA, driver):
    info = []

    UrlID = driver.find_elements_by_xpath(xpathToId)
    a_tags = driver.find_elements_by_xpath(xpathToA)
    for i in range(len(UrlID)):
        pair = {
            'urlID': UrlID[i].get_attribute('innerHTML'),
            'url': a_tags[i].get_attribute('href'),
            'title': a_tags[i].get_attribute('title')
        }
        info.append(pair)
    return info


def initWebDriver(pathToCRX):
    chop = webdriver.ChromeOptions()
    chop.add_extension(pathToCRX)
    driver = webdriver.Chrome(options=chop)
    return driver


def initReport(filePath, fields):
    df = pd.read_csv(filePath)  # or pd.read_excel(filename) for xls file
    if df.empty:
        with open(filePath, 'w', newline="") as file:
            csvwriter = csv.DictWriter(file, fieldnames=fields)
            csvwriter.writeheader()
            file.close()
    return


def cleaningOptionValue(option_value):
    result = option_value
    if '$' in option_value:
        index = option_value.find('$')
        result = option_value[:index]
    distracting_words = ['sale', 'scale']
    for word in distracting_words:
        if word in result:
            result = result.replace(word, '')

    if '/' in result:
        i = result.find('/')
        word1 = result[0:i]
        word2 = result[i:]
        result = ' '.join([word1, word2])
    return result


def selectActionLink(driver, title):
    all_links = driver.find_elements_by_xpath("//a[@class = 'action-link']")
    max_size = 0
    title_set = set(title.split())
    result = ""
    for link in all_links:
        isLink = link.get_attribute('target') == ""
        if isLink:
            compared = set(link.get_attribute('innerHTML').split())
            print(list(compared & title_set))
            intersec = len(list(compared & title_set))
            if intersec > max_size:
                max_size = intersec
                result = link
    if not result:
        result = all_links[0]
    return result


# This function ought to be site specific sincce
# each site has different rules of encoding and noisy chars
def cleanWords(raw_words, noisy_chars):
    return_words = raw_words.copy()
    index = 0
    print('start cleansing')
    for word in raw_words:
        for char in noisy_chars:
            if char in word:
                # print('removing {0} from {1}'.format(char, word))
                return_words[index] = return_words[index].replace(char, "")
                if return_words[index] == "":
                    return_words.pop(index)
                    index = index - 1
                else:
                    if char == '-':
                        word_to_split = return_words[index]
                        i = word.find('-')
                        word1 = word_to_split[0:i]
                        word2 = word_to_split[i:]
                        return_words.pop(index)
                        return_words.insert(index, word1)
                        return_words.insert(index+1, word2)
                        index = index + 1
        index = index + 1
    print('cleansing finished: {0}'.format(return_words))
    return return_words


def click_SelectBar(index, driver):
    driver.execute_script('document.getElementsByClassName({0})['.format(
        xpath_config.CLICKBAR_CLASSNAME) + str(index) + '].click()')
    return


# cleaning_tile 2.0
def filter_title(given_title, page_title):
    given_title = [title.lower() for title in given_title]
    page_title = [title.lower() for title in page_title]
    set_given = set(given_title)
    set_title = set(page_title)
    set_given = set_given - set_title
    print('Filtered before: {0}, Filtered after: {1}'.format(
        given_title, list(set_given)))
    return list(set_given)


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False
