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

def test_func(func,s1,s2):
    print('Comparison between {0} and {1} yields {2}'.format(s1, s2, func(s1,s2)))

# test_func(lcs,)