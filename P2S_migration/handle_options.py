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
            # print("Current child: " + child.get_attribute('outerHTML') + ' text: ' + child.get_attribute('textContent'))
            option_value = option_value + child.get_attribute('textContent')

        option_value = helper_funcs.cleaningOptionValue(option_value)
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
            # print("Current child: " + child.get_attribute('outerHTML') + ' text: ' + child.get_attribute('textContent'))
            option_value = option_value + child.get_attribute('textContent')
        
        option_value = helper_funcs.cleaningOptionValue(option_value)
        option_value = option_value.split(',')
        # option_value = (" ".join(option_value)).split()
    
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
