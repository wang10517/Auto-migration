## This file contains a list of xpath selecotrs needed by this module 
## to achieve its functionality. This file needs to be set per domain 

# Following constants appear in controller.py
PROCESSDOMAIN = 1
STARTSITEID = 2
PATHTODOMAINSOURCE = "Sites\Organizing Complex P2S migrations.xlsx"
PATHTOEXTENSION = '/Users/Shengkai/Downloads/PROWL-Toolbar_v2.13.1 (1).crx'

PRODUCTNAME_CLASSNAME = 'product-name'
ALL_SELECT_XPATH = '//div[@class = "product-variant-selector js-product-variant-selector"]//div[contains(id,selector)]//ul[@class = "buybox-dropdown__options js-basedropdown__options"]'
CLICKBAR_CLASSNAME = 'buybox-dropdown-selector'
SELECT_ATTR_CSS = 'div.product-variant-selector p'
OPTIONS_XPATH = ".//li" # connected to each child of all_selects

