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


# from selenium.webdriver.chrome.options import Options
import unittest
import time
import re
import openpyxl
import csv



#------------------------ Helper Functions ------------------------------------------# #
def importSiteStream(pathToSites,sheetName):
    workbook = openpyxl.load_workbook(pathToSites)
    worksheet = workbook[sheetName]
    return worksheet

def getSites(sheet):
    urls = []
    ## index here to be changed to sheet-specific
    for row in sheet.iter_rows(min_row=2, min_col= 6 , max_col=6):
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

def getEndInfo(xpathToId, xpathToA,driver):
    info = []

    UrlID = driver.find_elements_by_xpath(xpathToId)
    a_tags = driver.find_elements_by_xpath(xpathToA)
    for i in range(len(UrlID)):
        pair = {
            'urlID' : UrlID[i].get_attribute('innerHTML'),
            'url' : a_tags[i].get_attribute('href'),
            'title' : a_tags[i].get_attribute('title')
        }
        info.append(pair)
    return info

def initWebDriver(pathToCRX):
    chop = webdriver.ChromeOptions()
    chop.add_extension(pathToCRX)
    driver = webdriver.Chrome(options=chop)
    return driver

def scoringFuncCollections(str1,str2):
    s1 = str(str1).lower()
    s2 = str(str2).lower()
    # normalized_levenshtein = NormalizedLevenshtein()
    # leven_score = normalized_levenshtein.distance(s1,s2)
    # jarowinkler = JaroWinkler()
    # jar_score = jarowinkler.similarity(s1,s2)
    # cosine = Cosine(2)
    # p1 = cosine.get_profile(s1)
    # p2 = cosine.get_profile(s2)
    # cos_score = cosine.similarity_profiles(p1, p2)

    lcs = LongestCommonSubsequence()
    lcs_score = lcs.distance(s1, s2)

    # ave = (cos_score + leven_score + jar_score)/3

    return lcs_score/max([len(s1),len(s2)])


def longestSubstringFinder(string1, string2):
    if len(string1) > len(string2):
        return longestSubstringFinder(string2, string1)
    string1 = string1.lower()
    string2 = string2.lower()
    answer = ""
    len1, len2 = len(string1), len(string2)
    for i in range(len1):
        match = ""
        for j in range(len2):
            if (i + j < len1 and string1[i + j] == string2[j]):
                match += string2[j]
            else:
                if (len(match) > len(answer)): answer = match
                match = ""
    return len(answer)

def lcs(S,T):
    S = S.lower()
    T = T.lower()

    m = len(S)
    n = len(T)
    counter = [[0]*(n+1) for x in range(m+1)]
    longest = 0
    lcs_set = set()
    for i in range(m):
        for j in range(n):
            if S[i] == T[j]:
                c = counter[i][j] + 1
                counter[i+1][j+1] = c
                if c > longest:
                    lcs_set = set()
                    longest = c
                    lcs_set.add(S[i-c+1:i+1])
                elif c == longest:
                    lcs_set.add(S[i-c+1:i+1])

    return longest


def initReport(filePath, fields):
    df = pd.read_csv(filePath) # or pd.read_excel(filename) for xls file
    if df.empty:
        with open(filePath, 'w', newline = "") as file:
            csvwriter = csv.DictWriter(file,fieldnames = fields)
            csvwriter.writeheader()
            file.close()
    return

def cleaningOptionValue(option_value):
    result = option_value
    if '$' in option_value:
        index = option_value.find('$')
        result = option_value[:index]
    return result 

def handleOptions(csvwriter,index, options,cleansed_words, scoreFunc, foundThreshold,info, attr, driver):
    print('----- start handling options -----')

    found = False
    max_score = 0
    match_seg = ""
    match_option = ""
    all_options = []
    selected = ""
    if len(options) == 1:
        print('single option detected')

        single_option = options[0]
        option_value = ""       
        all_children = single_option.find_elements_by_xpath('./*')
        for child in all_children:
            print("Current child: " + child.get_attribute('outerHTML') + ' text: ' + child.get_attribute('textContent'))
            option_value = option_value + child.get_attribute('textContent')

        option_value = cleaningOptionValue(option_value)
        print('option value: ' + option_value)
        
        if ("one" in option_value or "One" in option_value) or option_value in cleansed_words:
            found = True
            csvwriter.writerow({
                'UrlID' : info['urlID'],
                'Url' : info['url'],
                'Title' : " ".join(cleansed_words),
                'Matched segm' : "single_case",
                "Matched Option" : "Single_case",
                "All options" : option_value,
                'Found' : found,
                'Attriubte' : attr
            })

            print("Don't care for this one")
            return False, None
        else:
            csvwriter.writerow({
                'UrlID' : info['urlID'],
                'Url' : info['url'],
                'Title' : " ".join(cleansed_words),
                'Matched segm' : "single_case",
                "Matched Option" : "Single_case",
                "All options" : option_value,
                'Found' : "out of stock or don't care",
                'Attriubte' : attr
            })
            print("Not sure")
            return False, None

    print('multiple options detected')
    for option in options:

        time.sleep(5)
        option_value = ""       
        all_children = option.find_elements_by_xpath('./*')
        for child in all_children:
            print("Current child: " + child.get_attribute('outerHTML') + ' text: ' + child.get_attribute('textContent'))
            option_value = option_value + child.get_attribute('textContent')
        
        option_value = cleaningOptionValue(option_value)
        option_value = option_value.split(',')
        option_value = (" ".join(option_value)).split()
    
        option_length = len(option_value)
        option_value = " ".join(option_value)
        print("Current option value: " + option_value)


        all_options.append(option_value)
        # for i in range(len(cleansed_words) - option_length + 1):
        #     test_seg = " ".join(cleansed_words[i:i+option_length])
        #     score = scoreFunc(test_seg,option_value)
        #     print("current test_seg: {0}, current option_value: {1}, score: {2}".format(test_seg, option_value, score))
        #     if score > max_score:
        #         print('replacing {0} with {1}'.format(match_seg+" : " + match_option, test_seg + " : " + option_value))
        #         max_score = score
        #         match_seg = test_seg
        #         match_option = option_value
        #         selected = option

        # What if we do a direct string-wise comparison?
        test_seg = " ".join(cleansed_words)
        score = scoreFunc(test_seg,option_value)
        test_reverse = " ".join(list(reversed(test_seg.split())))
        score = max([score, scoreFunc(test_reverse,option_value)])
        numbers_in_title = re.findall(r'\d+',test_seg)
        print("current test_seg: {0}, current option_value: {1}, score: {2}".format(test_seg, option_value, score))
        if score >= max_score:
            numbers_in_optionValue = re.findall(r'\d+',option_value)
            numbers_in_preOV = re.findall(r'\d+',match_option)
            if numbers_in_title:
                if len(set(numbers_in_title) & set(numbers_in_optionValue)) >= len(set(numbers_in_title) & set(numbers_in_preOV)):                
                    print('replacing {0} with {1}'.format(match_seg+" : " + match_option, test_seg + " : " + option_value))
                    max_score = score
                    match_seg = test_seg
                    match_option = option_value
                    selected = option
            else:
                    print('replacing {0} with {1}'.format(match_seg+" : " + match_option, test_seg + " : " + option_value))
                    max_score = score
                    match_seg = test_seg
                    match_option = option_value
                    selected = option 
            
    print('Final pair: {0},{1}'.format(match_seg, match_option))
    
    if max_score > foundThreshold:
        found = True
        print('Option Confirmed')
        # time.sleep(7)
        # click_SelectBar(index, driver)
        # time.sleep(12)
        # selected.click()
    else:
        print('Option failed to confirm')
        match_seg = 'N/A'
        match_option = 'N/A'

    csvwriter.writerow({
        'UrlID' : info['urlID'],
        'Url' : info['url'],
        'Title' : " ".join(cleansed_words),
        'Matched segm' : match_seg,
        "Matched Option" : match_option,
        "All options" : all_options,
        'Found' : found,
        'Attriubte' : attr
    })
    print('----- handling options End -----') 
    return found, selected

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
    
    # max_length = 0
    # result = ""
    # for link in all_links:
    #     isLink = link.get_attribute('target') == None
    #     if isLink:
    #         length = longestSubstringFinder(title,link.get_attribute('innerHTML'))
    #         if  length > max_length:
    #             result = link
    # return result
            



## This function ought to be site specific sincce
## each site has different rules of encoding and noisy chars
def cleanWords(raw_words, noisy_chars):
    return_words = raw_words.copy()
    index = 0
    print('start cleansing')
    for word in raw_words:
        for char in noisy_chars:
            if char in word:
                print('removing {0} from {1}'.format(char, word))
                return_words[index] = return_words[index].replace(char,"")
                if return_words[index] == "":
                    return_words.pop(index)
                    index = index -1
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
     driver.execute_script('document.getElementsByClassName("buybox-dropdown-selector")[' + str(index) + '].click()')
     return


## cleaning_tile 2.0
def filter_title(given_title, page_title):
    given_title = [title.lower() for title in given_title]
    page_title = [title.lower() for title in page_title]
    set_given = set(given_title)
    set_title = set(page_title)
    set_given = set_given - set_title
    print('Filtered before: {0}, Filtered out: {1}'.format(given_title, list(set_given)))
    return list(set_given)
#------------------------ Helper Functions End ------------------------------------------#



# --------------------------Test Setup ---------------------------------------------------#

print("----------Test Setup Starts----------")

print('loading the webdriver')

sheet = importSiteStream("Sites\Organizing Complex P2S migrations.xlsx","Migratable")
urls, domains = getSites(sheet)
## Load and configure the web driver
driver = initWebDriver('/Users/Shengkai/Downloads/PROWL-Toolbar_v2.13.1 (1).crx')

print('webdriver loaded') 

## Site id used for testing
site_id = 1
## Test instance for testing mutliple options
test_id = 0

print('testing {0},{1} url'.format(site_id,test_id+1))

driver.get(urls[site_id])
cur_domain = domains[site_id].value

print('handling login')

driver = handleLogin(driver)
time.sleep(3)
## this takes a lot of time
end_urls = getEndInfo('//td[@data-column = "urlId"]','//td[@class = "product__name"]/a',driver)
## Go to product test


## Init the log csv
fields = ['UrlID','Url','Title','Matched segm', 'Matched Option','All options','Found', 'Attriubte']
filePath = 'log_perDomain\\' + cur_domain + '.csv'
initReport(filePath, fields)

print("----------Test Setup Finished ----------")
# --------------------------Setup Finished ---------------------------------------------------#

# ---------------------------Test Zone-----------------------------------------------------#
for url in end_urls:
    print('testing {0},{1} url'.format('backcountry.com',test_id+1))

    driver.get(url['url'])
    URLID = url['urlID']
    raw_words = url['title'].split()
    ## The procedure starts here
    time.sleep(2)
    print("----------Testing Starts----------")
    print('Going to the prowl')
    time.sleep(5)
    prowl_tab = driver.find_element_by_xpath("//iframe[@id='prowl-add-url']")
    driver.switch_to.frame(prowl_tab)
    driver.find_element_by_xpath("//a[@title = 'Products on current page monitored by PROWL']").click()

    time.sleep(3)
    matched_link = selectActionLink(driver,end_urls[test_id]['title'])
    print(matched_link)
    print("The action link selected is: " + matched_link.get_attribute('innerHTML'))

    matched_link.click()

    time.sleep(2)

    print('Scout Clicked')

    try:
        driver.find_element_by_xpath("//select[@class = 'sc-gzVnrw gfDNes select2-hidden-accessible']//option[text() = 'SCOUT']").click()
        driver.switch_to.default_content()
    except:
        print('No monitored price found')
        with open(filePath, 'a', newline='') as file:
            csvwriter = csv.DictWriter(file,fieldnames = fields)
            csvwriter.writerow({
                    'UrlID' : end_urls[test_id]['urlID'],
                    'Url' : end_urls[test_id]['url'],
                    'Title' : end_urls[test_id]['title'],
                    'Matched segm' : "N/A",
                    "Matched Option" : "N/A",
                    "All options" : "N/A",
                    'Found' : "No monitored price found",
                    'Attriubte' : "N/A"
                })
        continue


    noisy_chars = ['-','(',')']
    clean_1 = cleanWords(raw_words,noisy_chars)
    page_title = driver.find_element_by_class_name('product-name').text
    cleansed_words = filter_title(clean_1, page_title.split())

    time.sleep(3)
    try: 
        all_selects = driver.find_elements_by_xpath('//div[@class = "product-variant-selector js-product-variant-selector"]//div[contains(id,selector)]//ul[@class = "buybox-dropdown__options js-basedropdown__options"]')
        pathToSelector = 'buybox-dropdown-selector'
        print('Getting click bars and title attributes')
        click_bars = driver.find_elements_by_class_name(pathToSelector)
    except:
        print('Failed to retrieve any product information')
        with open(filePath, 'a', newline='') as file:
            csvwriter = csv.DictWriter(file,fieldnames = fields)
            csvwriter.writerow({
                    'UrlID' : end_urls[test_id]['urlID'],
                    'Url' : end_urls[test_id]['url'],
                    'Title' : end_urls[test_id]['title'],
                    'Matched segm' : "N/A",
                    "Matched Option" : "N/A",
                    "All options" : "N/A",
                    'Found' : "Failed to get the product",
                    'Attriubte' : "N/A"
                })
        continue


    index = 0
    need_parameter = False
    title_attriubtes = driver.find_elements_by_css_selector('div.product-variant-selector p')
    options_to_add = []

    print('Start writing to the file:')

    with open(filePath, 'a', newline='') as file:
        csvwriter = csv.DictWriter(file,fieldnames = fields)
        for select_tab in all_selects:
            options = select_tab.find_elements_by_xpath(".//li")
            found_threshold = 2
            found = False
            attr = title_attriubtes[index].get_attribute("innerHTML").replace(":","").split()
            if attr[-2] == '&amp;':
                attr = "/".join([attr[-3], attr[-1]])
                if attr == 'style/size':
                    attr = 'Size/Color'
            else:
                attr = attr[-1]

            print("Current processing select bar: " + attr)

            local_check_para, selected = handleOptions(csvwriter , index,  options , cleansed_words, lcs, found_threshold , end_urls[test_id] , attr, driver)
            if local_check_para:
                need_parameter = True
                options_to_add.append({
                    "attribute" : attr,
                    "click_bar" : index,
                    "option_tab" : selected
                        })
            index = index + 1

        file.close()

    print('file closed')



    prowl_tab = driver.find_element_by_xpath("//iframe[@id='prowl-add-url']")
    driver.switch_to.frame(prowl_tab)
    check = driver.find_element_by_xpath('//label[@for = "show-in-reports"]//input').is_selected()
    if not check:
        driver.find_element_by_xpath('//label[@for = "show-in-reports"]').click()
        print('show in report selected')

    if need_parameter:
        if not driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
            driver.find_element_by_xpath('//label[@for = "is-params-needed"]').click()
            print('need parameter select')
    else:
        if  driver.find_element_by_xpath('//label[@for = "is-params-needed"]//input').is_selected():
            driver.find_element_by_xpath('//label[@for = "is-params-needed"]').click()
            print('need parameter de-select')

    driver.find_elements_by_tag_name('button')[0].click()
    time.sleep(3)

    ## Delete any preexisting parameter settings if any
    delete_buttons = driver.find_elements_by_class_name('fa-close')
    for db in delete_buttons:
        db.click()
        print('One previous parameter deleted')
        time.sleep(5)
                

    if need_parameter:
        print('adding options')
        for action in options_to_add:
            time.sleep(5)
            driver.find_element_by_xpath('//button[text() = "Add Option"]').click()
            driver.switch_to.default_content()
            time.sleep(10)
            click_SelectBar(action['click_bar'], driver)
            time.sleep(5)
            action['option_tab'].click()
            time.sleep(5)
            click_SelectBar(action['click_bar'], driver)
            time.sleep(5)
            action['option_tab'].click()
            print('option clicked')
            time.sleep(3)
            prowl_tab = driver.find_element_by_xpath("//iframe[@id='prowl-add-url']")
            driver.switch_to.frame(prowl_tab)
            # pre = False
            # try:
            #     all_existing_options = driver.find_element_by_xpath('//option/text() = {0}'.format(action['attribute']))
            #     pre = True
            #     print('previous option detected')
            # except: 
            #     print("no preivous options detected")


            
            complex_options = driver.find_elements_by_class_name('complex-option')
            # complex_options[-1].find_element_by_xpath("//option[contains(text(),'" + action['attribute'] + "')]").click()
            select = Select(complex_options[-1].find_element_by_xpath('./select'))
            try:
                select.select_by_visible_text(action['attribute'])
            except:
                try: 
                    select.select_by_value(action['attribute'].lower())
                except:
                    complex_options[-1].find_element_by_xpath("//option[contains(text(),'" + action['attribute'] + "')]").click()

            print('current_action finished: ' + action['attribute'])
        driver.find_element_by_xpath('//button[text() = "Save"]').click()
        time.sleep(5)
        driver.find_elements_by_class_name('success')[1].click()
        print('Procedure finished & saved')


    else:
        driver.find_elements_by_tag_name('button')[0].click()
        print('Procedure finished & saved')

    test_id = test_id + 1
    print('-------- Testing finished  --------')

# ---------------------------Test Zone End -------------------------------------------------#
