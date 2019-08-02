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
import helper_funcs
import handle_options
import scoring_metrix
import xpath_config

# --------------------------Test Setup ---------------------------------------------------#

print("----------Test Setup Starts----------")

print('loading the webdriver')
pathToDomainSource = xpath_config.PATHTODOMAINSOURCE
sheet = helper_funcs.importSiteStream(pathToDomainSource, "Migratable")
urls, domains = helper_funcs.getSites(sheet)
# Load and configure the web driver
driver = helper_funcs.initWebDriver(xpath_config.PATHTOEXTENSION)

print('webdriver loaded')

# Site id used for testing
domain_id = xpath_config.PROCESSDOMAIN
# Test instance for testing mutliple options
start_site_id = xpath_config.STARTSITEID

print('testing {0},{1} url'.format(domain_id, start_site_id+1))

driver.get(urls[domain_id])
cur_domain = domains[domain_id].value

print('handling login')

driver = helper_funcs.handleLogin(driver)
time.sleep(3)
# this takes a lot of time
end_urls = helper_funcs.getEndInfo(
    '//td[@data-column = "urlId"]', '//td[@class = "product__name"]/a', driver)
# Go to product test


# Init the log csv
fields = ['UrlID', 'Url', 'Title', 'Matched segm',
          'Matched Option', 'All options', 'Found', 'Attriubte']
filePath = 'log_perDomain/' + cur_domain[:-4] + '.csv'
helper_funcs.initReport(filePath, fields)

print("----------Test Setup Finished ----------")
# --------------------------Setup Finished ---------------------------------------------------#

# ---------------------------Test Zone-----------------------------------------------------#
print("---------- URL stream starts ----------")

for index, url in enumerate(end_urls):
    if index >= start_site_id:
        test_id = index
        print('testing domain:{0}, with url number: {1}'.format(
            cur_domain, test_id+1))
        driver.get(url['url'])
        URLID = url['urlID']
        raw_words = url['title'].split()
        # The procedure starts here
        print('Going to the prowl')

        try:
            time.sleep(5)
            prowl_tab = driver.find_element_by_xpath("//iframe[@id='prowl-add-url']")
            driver.switch_to.frame(prowl_tab)
            driver.find_element_by_xpath("//a[@title = 'Products on current page monitored by PROWL']").click()
        except:
            print('Toobar loading failed; Trying to load it again...')
            try:
                driver.get(url['url'])
                WebDriverWait(driver, 10).until(EC.presence_of_element_located(
                    (By.XPATH, "//iframe[@id='prowl-add-url']")))
            except:
                print('Cannot load the toolbar')
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

        print('Tool bar loaded properly')

        time.sleep(5)

        try:
            matched_link = helper_funcs.selectActionLink(driver, end_urls[test_id]['title'])
        except:
            print('No action link found, need to add manually(To be automated)')
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

        print("The action link selected is: " +
              matched_link.get_attribute('innerHTML'))

        matched_link.click()

        try:
            time.sleep(10)
            driver.find_element_by_xpath("//select[@class = 'sc-gzVnrw gfDNes select2-hidden-accessible']//option[text() = 'SCOUT']").click()
            print('Scout Clicked')
        except:
            print('cannot click to scout')
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

        noisy_chars = ['-', '(', ')','&']
        clean_1 = helper_funcs.cleanWords(raw_words, noisy_chars)

        try:
            page_title = driver.find_element_by_class_name(xpath_config.PRODUCTNAME_CLASSNAME).text
            cleansed_words = helper_funcs.filter_title(clean_1, page_title.split())
        except:
            print('Failed to retrieve any product information')
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
        need_parameter = True
        try:
            all_selects = driver.find_elements_by_xpath(xpath_config.ALL_SELECT_XPATH)
        except:
            print('No parameter needed')
            need_parameter = False
        
        click_bars_t1 = [] 
        click_bars_t2 = []
        click_bars_t3 = []

        if need_parameter:
            print('Getting click bars and title attributes')
            try:
                click_bars_t1 = driver.find_elements_by_xpath(xpath_config.CLICKBAR_XPATH_t1)
            except:
                print('No drop down bar detected')
            try:
                click_bars_t2 = driver.find_elements_by_xpath(xpath_config.CLICKBAR_XPATH_t2)
            except:
                print('No radio button found')
            try:
                click_bars_t3 = driver.find_elements_by_xpath(xpath_config.CLICKBAR_XPATH_t3)
            except:
                print('No checkbox found')
            

            index_inner = 0
            title_attriubtes = driver.find_elements_by_xpath(xpath_config.SELECT_ATTR_XPATH)
            options_to_add = []

            print('Start writing to the file:')

            with open(filePath, 'a', newline='') as file:
                csvwriter = csv.DictWriter(file, fieldnames=fields)
                for select_tab in all_selects:
                    format = select_tab.find_element_by_xpath('./div').get_attribute('class')
                    type = 0
                    if format == 'dropdown-format':
                        options = select_tab.find_elements_by_xpath(xpath_config.OPTIONS_XPATH_t1)
                        type = 1
                    elif format == 'radio-format':
                        options = select_tab.find_elements_by_xpath(xpath_config.OPTIONS_XPATH_t2)
                        type = 2
                    else:
                        type = 3
                        options = select_tab.find_elements_by_xpath(xpath_config.OPTIONS_XPATH_t3)

                    found_threshold = 2
                    found = False
                    rid_words = ['Options',':']
                    attr = title_attriubtes[index_inner].get_attribute(
                        "innerHTML")
                    for word in rid_words:
                        if word in attr:
                            attr = attr.replace(word, '')
                    attr = ' '.join(attr.split())
                    # if attr[-2] == '&amp;':
                    #     attr = "/".join([attr[-3], attr[-1]])
                    #     if attr == 'style/size':
                    #         attr = 'Size/Color'
                    # else:
                    #     attr = attr[-1]
                    # attr = ''
                    if attr == 'Ordering' or attr == 'Order':
                        attr = 'Type'
                    if 'Size' in attr:
                        attr = 'Size' 

                    print("Current processing select bar: " + attr)

                    local_check_para, selected = handle_options.handleOptions(
                        csvwriter, index_inner,  options, cleansed_words, scoring_metrix.lcs, found_threshold, end_urls[test_id], attr, driver, type)
                    if local_check_para:
                        need_parameter = True
                        options_to_add.append({
                            "attribute": attr,
                            "option_tab": selected,
                            "Dropdown" : format == 'dropdown-format'
                        })
                    index_inner = index_inner + 1

                file.close()

            print('file closed')

        prowl_tab = driver.find_element_by_xpath(
            "//iframe[@id='prowl-add-url']")
        driver.switch_to.frame(prowl_tab)
        check = driver.find_element_by_xpath(
            '//label[@for = "show-in-reports"]//input').is_selected()
        if not check:
            driver.find_element_by_xpath(
                '//label[@for = "show-in-reports"]').click()
            print('show in report selected')

        if need_parameter:
            if not driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
                driver.find_element_by_xpath(
                    '//label[@for = "is-params-needed"]').click()
                print('need parameter select')
        else:
            if driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
                driver.find_element_by_xpath(
                    '//label[@for = "is-params-needed"]').click()
                print('need parameter de-select')

        time.sleep(5)
        driver.find_elements_by_tag_name('button')[0].click()

        try:
            time.sleep(5)
            delete_buttons = driver.find_elements_by_class_name('fa-close')
        except:
            print('cannot load the adding parameter page')
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
            print('One previous parameter deleted')
            time.sleep(3)

        if need_parameter:
            print('adding options')
            for action in options_to_add:
                time.sleep(10)
                try:
                    driver.find_element_by_xpath(
                        '//button[text() = "Add Option"]').click()
                except:
                    try:
                        driver.find_element_by_xpath(
                            '//button[text() = "Add Option"]').click()
                    except:
                        with open(filePath, 'a', newline='') as file:
                            csvwriter = csv.DictWriter(file, fieldnames=fields)
                            csvwriter.writerow({
                                'UrlID': end_urls[test_id]['urlID'],
                                'Url': end_urls[test_id]['url'],
                                'Title': end_urls[test_id]['title'],
                                'Matched segm': "N/A",
                                "Matched Option": "N/A",
                                "All options": "N/A",
                                'Found': "cannot add parameter",
                                'Attriubte': "N/A"
                            })
                        continue
                        

                time.sleep(5)
                driver.switch_to.default_content()
                if action['Dropdown']:
                    cur_bar = click_bars_t1.pop(0)
                    cur_bar.click()
                    time.sleep(5)
                    action['option_tab'].click()
                    time.sleep(10)
                    cur_bar.click()
                    time.sleep(5)
                    action['option_tab'].click()
                else:
                    action['option_tab'].click()
                    action['option_tab'].click()
                print('option clicked')
                time.sleep(5)
                prowl_tab = driver.find_element_by_xpath(
                    "//iframe[@id='prowl-add-url']")
                driver.switch_to.frame(prowl_tab)
                # pre = False
                # try:
                #     all_existing_options = driver.find_element_by_xpath('//option/text() = {0}'.format(action['attribute']))
                #     pre = True
                #     print('previous option detected')
                # except:
                #     print("no preivous options detected")

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

                print('current_action finished: ' + action['attribute'])
            try:
                driver.find_element_by_xpath('//button[text() = "Save"]').click()
            except:
                print('The url could not be saved')
                continue
            driver.find_elements_by_class_name('success')[1].click()
            print('Procedure finished & saved')

        else:
            driver.find_elements_by_tag_name('button')[0].click()
            print('Procedure finished & saved')

        print("----------URL {0} ends ----------".format(index))

print("---------- URL stream ends ----------")

# ---------------------------Test Zone End -------------------------------------------------#
