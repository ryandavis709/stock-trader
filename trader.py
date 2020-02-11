import os
import settings
from pprint import pprint
import alphavantage
import alpha_vantage
import json
import requests
from selenium import webdriver

if __name__ == "__main__":
    print("hello world")
    print(os.getenv("API_KEY"))


    driver = webdriver.Chrome()
    driver.get("http://finance.yahoo.com/gainers")

    elem = driver.find_element_by_name
    table = driver.find_element_by_xpath("//table[@class='W(100%)']/tbody")
    row = table.find_element_by_xpath(".//tr[@class='simpTblRow Bgc($extraLightBlue):h BdB Bdbc($finLightGrayAlt) Bdbc($tableBorderBlue):h H(32px) Bgc(white) ']")
    while row:
        symbol = row.find_element_by_xpath(".//td[1]").text
        price = row.find_element_by_xpath(".//td[3]").text
        change = row.find_element_by_xpath(".//td[5]").text
        volume = row.find_element_by_xpath(".//td[7]").text
        print(symbol, price, change, volume)
        row = row.find_element_by_xpath(".//following-sibling::tr")

    symbols = ['TSLA',"AAPL","PDD"]


def query_stocks(symbols):
    API_URL = "https://www.alphavantage.co/query"
    for symbol in symbols:
        data = { "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol,
        "interval" : "1min",
        "datatype": "json",
        "apikey": os.getenv("API_KEY") }
        response = requests.get(API_URL, data)
        data = response.json()
        print(symbol)
        a = (data['Time Series (1min)'])
        keys = (a.keys())
        newest_key = list(keys)[0]
        print(newest_key + " " + str(a[newest_key]))
        #print( newest_key + " " + keys[newest_key])
