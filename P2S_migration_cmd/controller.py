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
import sys
import helper_funcs
import handle_options
import scoring_metrix
import xpath_config
# --------------------------Test Setup ---------------------------------------------------#

sys.stdout.write("---------- URL stream starts ---------" + "\n")
f.write("---------- URL stream starts ---------" + "\n")


sys.stdout.write('loading the webdriver' + "\n")
f.write('loading the webdriver' + "\n")
pathToDomainSource = xpath_config.PATHTODOMAINSOURCE
sheet = helper_funcs.importSiteStream(pathToDomainSource, "Migratable")
urls, domains = helper_funcs.getSites(sheet)
# Load and configure the web driver
driver = helper_funcs.initWebDriver(xpath_config.PATHTOEXTENSION)

sys.stdout.write('webdriver loaded' + "\n")
f.write('webdriver loaded' + "\n")

# Site id used for testing
domain_id = xpath_config.PROCESSDOMAIN
# Test instance for testing mutliple options
start_site_id = xpath_config.STARTSITEID

sys.stdout.write('testing {0},{1} url'.format(domain_id, start_site_id+1) + "\n")
f.write('testing {0},{1} url'.format(domain_id, start_site_id+1) + "\n")

driver.get(urls[domain_id])
cur_domain = domains[domain_id].value

sys.stdout.write('handling login' + "\n")
f.write('handling login' + "\n")

driver = helper_funcs.handleLogin(driver)
time.sleep(3)
# this takes a lot of time
end_urls = helper_funcs.getEndInfo(
    '//td[@data-column = "urlId"]', '//td[@class = "product__name"]/a', driver)
# Go to product test


# Init the log csv
fields = ['UrlID', 'Url', 'Title', 'Matched segm',
          'Matched Option', 'All options', 'Found', 'Attriubte']
filePath = 'log_perDomain\\' + cur_domain + '.csv'
helper_funcs.initReport(filePath, fields)

stream_log = open('log.txt','a')

sys.stdout.write("----------Test Setup Finished ----------" + "\n")
f.write("----------Test Setup Finished ----------" + "\n")
# --------------------------Setup Finished ---------------------------------------------------#

# ---------------------------Test Zone-----------------------------------------------------#
sys.stdout.write("---------- URL stream starts ----------" + "\n")
f.write("---------- URL stream starts ----------" + "\n")

for index, url in enumerate(end_urls):
    if index >= start_site_id:
        test_id = index
        sys.stdout.write('testing domain:{0}, with url number: {1}'.format(
            cur_domain, test_id+1))
        driver.get(url['url'])
        URLID = url['urlID']
        raw_words = url['title'].split()
        # The procedure starts here
        sys.stdout.write('Going to the prowl' + "\n")
f.write('Going to the prowl' + "\n")

        try:
            time.sleep(5)
            prowl_tab = driver.find_element_by_xpath("//iframe[@id='prowl-add-url']")
            driver.switch_to.frame(prowl_tab)
            driver.find_element_by_xpath("//a[@title = 'Products on current page monitored by PROWL']").click()
        except:
            sys.stdout.write('Toobar loading failed; Trying to load it again...' + "\n")
f.write('Toobar loading failed; Trying to load it again...' + "\n")
            try:
                driver.get(url['url'])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//iframe[@id='prowl-add-url']")))
            except:
                sys.stdout.write('Cannot load the toolbar' + "\n")
f.write('Cannot load the toolbar' + "\n")
                with open(filePath, 'a', newline='') as file:
                    csvwriter = csv.DictWriter(file, fieldnames=fields)
                    csvwriter.writerow({
                        'UrlID': end_urls[test_id]['urlID'],
                        'Url': end_urls[test_id]['url'],
                        'Title': end_urls[test_id]['title'],
                        'Matched segm': "N/A",
                        "Matched Option": "N/A",
                        "All options": "N/A",
                        'Found': "Tool bar not loading properly",
                        'Attriubte': "N/A"
                    })
                continue

        sys.stdout.write('Tool bar loaded properly' + "\n")
f.write('Tool bar loaded properly' + "\n")

        time.sleep(5)

        try:
            matched_link = helper_funcs.selectActionLink(driver, end_urls[test_id]['title'])
        except:
            sys.stdout.write('No action link found, need to add manually(To be automated)' + "\n")
f.write('No action link found, need to add manually(To be automated)' + "\n")
            with open(filePath, 'a', newline='') as file:
                csvwriter = csv.DictWriter(file, fieldnames=fields)
                csvwriter.writerow({
                    'UrlID': end_urls[test_id]['urlID'],
                    'Url': end_urls[test_id]['url'],
                    'Title': end_urls[test_id]['title'],
                    'Matched segm': "N/A",
                    "Matched Option": "N/A",
                    "All options": "N/A",
                    'Found': "No action link documented",
                    'Attriubte': "N/A"
                })
                continue

        sys.stdout.write("The action link selected is: " +
              matched_link.get_attribute('innerHTML'))

        matched_link.click()

        try:
            time.sleep(15)
            driver.find_element_by_xpath("//select[@class = 'sc-gzVnrw gfDNes select2-hidden-accessible']//option[text() = 'SCOUT']").click()
            sys.stdout.write('Scout Clicked' + "\n")
f.write('Scout Clicked' + "\n")
        except:
            sys.stdout.write('cannot click to scout' + "\n")
f.write('cannot click to scout' + "\n")
            with open(filePath, 'a', newline='') as file:
                csvwriter = csv.DictWriter(file, fieldnames=fields)
                csvwriter.writerow({
                    'UrlID': end_urls[test_id]['urlID'],
                    'Url': end_urls[test_id]['url'],
                    'Title': end_urls[test_id]['title'],
                    'Matched segm': "N/A",
                    "Matched Option": "N/A",
                    "All options": "N/A",
                    'Found': "cannot click to scout",
                    'Attriubte': "N/A"
                })
            continue

        driver.switch_to.default_content()

        noisy_chars = ['-', '(', ')']
        clean_1 = helper_funcs.cleanWords(raw_words, noisy_chars)

        try:
            page_title = driver.find_element_by_class_name(xpath_config.PRODUCTNAME_CLASSNAME).text
            cleansed_words = helper_funcs.filter_title(clean_1, page_title.split())
            all_selects = driver.find_elements_by_xpath(xpath_config.ALL_SELECT_XPATH)
            pathToSelector = xpath_config.CLICKBAR_CLASSNAME
            sys.stdout.write('Getting click bars and title attributes' + "\n")
f.write('Getting click bars and title attributes' + "\n")
            click_bars = driver.find_elements_by_class_name(pathToSelector)
        except:
            sys.stdout.write('Failed to retrieve any product information' + "\n")
f.write('Failed to retrieve any product information' + "\n")
            with open(filePath, 'a', newline='') as file:
                csvwriter = csv.DictWriter(file, fieldnames=fields)
                csvwriter.writerow({
                    'UrlID': end_urls[test_id]['urlID'],
                    'Url': end_urls[test_id]['url'],
                    'Title': end_urls[test_id]['title'],
                    'Matched segm': "N/A",
                    "Matched Option": "N/A",
                    "All options": "N/A",
                    'Found': "Failed to get the product",
                    'Attriubte': "N/A"
                })
            continue

        index = 0
        need_parameter = False
        title_attriubtes = driver.find_elements_by_css_selector(xpath_config.SELECT_ATTR_CSS)

        options_to_add = []

        sys.stdout.write('Start writing to the file:' + "\n")
f.write('Start writing to the file:' + "\n")

        with open(filePath, 'a', newline='') as file:
            csvwriter = csv.DictWriter(file, fieldnames=fields)
            for select_tab in all_selects:
                options = select_tab.find_elements_by_xpath(xpath_config.OPTIONS_XPATH)
                found_threshold = 2
                found = False
                attr = title_attriubtes[index].get_attribute(
                    "innerHTML").replace(":", "").split()
                if attr[-2] == '&amp;':
                    attr = "/".join([attr[-3], attr[-1]])
                    if attr == 'style/size':
                        attr = 'Size/Color'
                else:
                    attr = attr[-1]

                sys.stdout.write("Current processing select bar: " + attr + "\n")
f.write("Current processing select bar: " + attr + "\n")

                local_check_para, selected = handle_options.handleOptions(
                    csvwriter, index,  options, cleansed_words, scoring_metrix.lcs, found_threshold, end_urls[test_id], attr, driver)
                if local_check_para:
                    need_parameter = True
                    options_to_add.append({
                        "attribute": attr,
                        "click_bar": index,
                        "option_tab": selected
                    })
                index = index + 1

            file.close()

        sys.stdout.write('file closed' + "\n")
f.write('file closed' + "\n")

        prowl_tab = driver.find_element_by_xpath(
            "//iframe[@id='prowl-add-url']")
        driver.switch_to.frame(prowl_tab)
        check = driver.find_element_by_xpath(
            '//label[@for = "show-in-reports"]//input').is_selected()
        if not check:
            driver.find_element_by_xpath(
                '//label[@for = "show-in-reports"]').click()
            sys.stdout.write('show in report selected' + "\n")
f.write('show in report selected' + "\n")

        if need_parameter:
            if not driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
                driver.find_element_by_xpath(
                    '//label[@for = "is-params-needed"]').click()
                sys.stdout.write('need parameter select' + "\n")
f.write('need parameter select' + "\n")
        else:
            if driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
                driver.find_element_by_xpath(
                    '//label[@for = "is-params-needed"]').click()
                sys.stdout.write('need parameter de-select' + "\n")
f.write('need parameter de-select' + "\n")

        driver.find_elements_by_tag_name('button')[0].click()

        try:
            time.sleep(5)
            delete_buttons = driver.find_elements_by_class_name('fa-close')
        except:
            sys.stdout.write('cannot load the adding parameter page' + "\n")
f.write('cannot load the adding parameter page' + "\n")
            with open(filePath, 'a', newline='') as file:
                csvwriter = csv.DictWriter(file, fieldnames=fields)
                csvwriter.writerow({
                    'UrlID': end_urls[test_id]['urlID'],
                    'Url': end_urls[test_id]['url'],
                    'Title': end_urls[test_id]['title'],
                    'Matched segm': "N/A",
                    "Matched Option": "N/A",
                    "All options": "N/A",
                    'Found': "cannot load the adding parameter page",
                    'Attriubte': "N/A"
                })
            continue
        # Delete any preexisting parameter settings if any
        for db in delete_buttons:
            db.click()
            sys.stdout.write('One previous parameter deleted' + "\n")
f.write('One previous parameter deleted' + "\n")
            time.sleep(3)

        if need_parameter:
            sys.stdout.write('adding options' + "\n")
f.write('adding options' + "\n")
            for action in options_to_add:
                time.sleep(10)
                driver.find_element_by_xpath(
                    '//button[text() = "Add Option"]').click()
                driver.switch_to.default_content()
                helper_funcs.click_SelectBar(action['click_bar'], driver)
                time.sleep(5)
                action['option_tab'].click()
                time.sleep(5)
                helper_funcs.click_SelectBar(action['click_bar'], driver)
                time.sleep(5)
                action['option_tab'].click()
                sys.stdout.write('option clicked' + "\n")
f.write('option clicked' + "\n")
                time.sleep(5)
                prowl_tab = driver.find_element_by_xpath(
                    "//iframe[@id='prowl-add-url']")
                driver.switch_to.frame(prowl_tab)
                # pre = False
                # try:
                #     all_existing_options = driver.find_element_by_xpath('//option/text() = {0}'.format(action['attribute']))
                #     pre = True
                #     sys.stdout.write('previous option detected' + "\n")
f.write('previous option detected' + "\n")
                # except:
                #     sys.stdout.write("no preivous options detected" + "\n")
f.write("no preivous options detected" + "\n")

                complex_options = driver.find_elements_by_class_name(
                    'complex-option')
                # complex_options[-1].find_element_by_xpath("//option[contains(text(),'" + action['attribute'] + "')]").click()
                select = Select(
                    complex_options[-1].find_element_by_xpath('./select'))
                try:
                    select.select_by_visible_text(action['attribute'])
                except:
                    try:
                        select.select_by_value(action['attribute'].lower())
                    except:
                        complex_options[-1].find_element_by_xpath(
                            "//option[contains(text(),'" + action['attribute'] + "')]").click()

                sys.stdout.write('current_action finished: ' + action['attribute'] + "\n")
f.write('current_action finished: ' + action['attribute'] + "\n")
            driver.find_element_by_xpath('//button[text() = "Save"]').click()
            driver.find_elements_by_class_name('success')[1].click()
            sys.stdout.write('Procedure finished & saved' + "\n")
f.write('Procedure finished & saved' + "\n")

        else:
            driver.find_elements_by_tag_name('button')[0].click()
            sys.stdout.write('Procedure finished & saved' + "\n")
f.write('Procedure finished & saved' + "\n")

        sys.stdout.write("----------URL {0} ends ----------".format(index) + "\n")
f.write("----------URL {0} ends ----------".format(index) + "\n")

sys.stdout.write("---------- URL stream ends ----------" + "\n")
f.write("---------- URL stream ends ----------" + "\n")

# ---------------------------Test Zone End -------------------------------------------------#
