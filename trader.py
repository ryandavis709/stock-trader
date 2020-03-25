import os
import settings
from pprint import pprint
#import alphavantage
#import alpha_vantage
import json
import requests
from selenium import webdriver
import time
import datetime

#todo
# only run when market is open
# give portfolio update every hour
#   current holdings, current profit holdings are stock and cash balances
# repeat the cycle upon market open every morning
"""
    Author: Ryan Davis
    Date: 3/25/2020

    Class to contain all of the necessary funcitons to deal with the API calls
    of buying, selling, and querying stock prices

"""
class Stock_Trader:
    """
        Author: Ryan Davis
        Date: 3/25/2020

        Initializes all of the necessary data for stock_trader class

    """
    def __init__(self):
        self.API_URL = "https://www.alphavantage.co/query"
        self.symbols = []
        self.bought_stocks = []
        self.capital = 1000
        self.risk = .1
    """
        Author: Ryan Davis
        Date: 3/25/2020

        Gets SMA (moving average) of requested stock

        Arguments:
            symbol: dict containing current stock information
            self: instance of stock_trader class

        Returns:
            symbol: updated dict containing current stock information,
                basically adds SMA information to stock information
    """
    def getSMAhigh(self,symbol):
        SMA_high = { "function": "SMA",
        "symbol": symbol['symbol'],
        "interval": "1min",
        "time_period":"200",
        "series_type":"high",
        "apikey":os.getenv("API_KEY") }
        response = requests.get(self.API_URL, SMA_high)
        data = response.json()
        a = data['Technical Analysis: SMA']
        keys = a.keys()
        newest_key = list(keys)[0]
        #print(symbol['symbol'] + " " + str(newest_key) + " " + str(a[newest_key]["SMA"]))
        symbol["SMA"] = float(a[newest_key]["SMA"])
        return symbol
    """
        Author: Ryan Davis
        Date: 3/23/2020

        Gets current price of the stock

        Arguments:
            symbol: dict containing current stock symbol and information
            self: instance of stock_trader class
        Returns:
            None
    """
    def getCurrentPrice(self,symbol):
        data = { "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol['symbol'],
        "interval" : "1min",
        "datatype": "json",
        "apikey": os.getenv("API_KEY") }
        response = requests.get(self.API_URL, data)
        data = response.json()
        a = (data['Time Series (1min)'])
        keys = (a.keys())
        newest_key = list(keys)[0]
        #print(str(a[newest_key]))
        symbol["Current_Price"] = float(a[newest_key]["1. open"])
        return symbol
    """
        Author: Ryan Davis
        Date: 3/23/2020

        Buys stock at current price. Only uses risk% of total capital per trade, updates current capital

        Arguments:
            symbol: dict contain current stock symbol and information
            self: instance of stock_trader class
        Returns:
            num_shares: number of shares bought of current stock
    """
    def buy_stock(self, symbol):
        num_shares = self.capital * self.risk / symbol['Current_Price']

        print("Bought {} shares of {}".format(num_shares,symbol['symbol']))

        return num_shares
    """
        Author: Ryan Davis
        Date: 3/23/2020

        Sells stock at current price

        Arguments:
            symbol: dict containing current stock symbol and information
            self: current instance of stock_trader class
        Returns:
            None
    """
    def sell_stock(self, symbol):
        change = (symbol["Shares_Bought"] * symbol["Current_Price"]) - (symbol["Shares_Bought"] * symbol["Bought_Price"])
        if change > 0:
            print("Sold all of {} for {} in profit!".format(symbol['symbol'], change))
        else:
            print("Sold all of {} for a {} loss!".format(symbol['symbol'], change))


"""
    Author: Ryan Davis
    Date: 3/23/2020

    Scapes yahoo finance gainers for the first page of the most changed stocks today, only

    Arguments:
        None
    Returns:
        stocks_to_watch: array of of stocks, each containing symbol, price, change, volume
"""
def get_stocks_to_watch():
    stocks_to_watch = []

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
        if ("M" in volume):
            stock = {"symbol":symbol, "price":price,"change":change, "volume":volume}
            stocks_to_watch.append(stock)
        try:
            row = row.find_element_by_xpath(".//following-sibling::tr")
        except:
            print("no more rows!")
            return stocks_to_watch

if __name__ == "__main__":
    trader = Stock_Trader()
    count = 0
    current_assets = 0
    stocks_to_watch = get_stocks_to_watch()
    trader.symbols = stocks_to_watch[:5]

    for symbol in trader.symbols:
        symbol = trader.getSMAhigh(symbol)
        print(symbol)

    time.sleep(60)
    trading = True
    while trading:
        for symbol in trader.symbols:
            symbol = trader.getCurrentPrice(symbol)
            if symbol["Current_Price"] >= symbol["SMA"]:
                if symbol["symbol"] not in trader.bought_stocks:
                    trader.bought_stocks.append(symbol['symbol'])
                    print("\nBuying {} @ {} per share".format(symbol["symbol"], symbol["Current_Price"]))
                    symbol["Shares_Bought"] = trader.buy_stock(symbol)
                    symbol["Sold"] = False
                    symbol["Last_Price"] = symbol["Current_Price"]
                    symbol["Bought_Price"] = symbol["Current_Price"]
                    symbol["Exit"] = symbol["Current_Price"] * .97
                    print("Setting exit @ {}\n".format(symbol["Exit"]))
                    trader.capital -= (symbol["Shares_Bought"] * symbol["Current_Price"])
                    current_assets = current_assets + (symbol["Shares_Bought"] * symbol["Current_Price"])
                    print("Current account balance: {}\n".format(trader.capital))
                if symbol["Current_Price"] > symbol["Last_Price"]:
                    current_assets = current_assets - (symbol["Shares_Bought"] * symbol["Last_Price"])
                    current_assets = current_assets + (symbol["Shares_Bought"] * symbol["Current_Price"])
                    symbol["Last_Price"] = symbol["Current_Price"]
                    symbol["Exit"] = symbol["Current_Price"] * .97
                    print("\n{} rose to {}, updating exit to {}\n".format(symbol['symbol'], symbol['Current_Price'], symbol['Exit']))
                if symbol["Current_Price"] <= symbol["Exit"]:
                    if symbol["Sold"] == False:
                        print("\nSold {} @ {}".format(symbol['symbol'], symbol['Current_Price']))
                        trader.sell_stock(symbol)
                        trader.capital += (symbol["Shares_Bought"] * symbol["Current_Price"])
                        current_assets = current_assets - (symbol["Shares_Bought"] * symbol["Current_Price"])
                        symbol['Sold'] = True
                        print("Current account balance: {}\n".format(trader.capital))
                    #trader.bought_stocks.remove(symbol['symbol'])
        if count % 2 == 0:
            print("Current account summary: \n\tAssets: {} \n\tCash: {} \n\tTotal: {} \n\tgains/losses: {}\n".format(current_assets, trader.capital, current_assets + trader.capital, (current_assets + trader.capital) - 1000))
        count += 1
        time.sleep(60)

    # get stocks to monitor
    # get SMA_high
    # wait 1 minute
    # get SMA_low
    # wait 1 minute
    # get current price
    # wait 1 minute, etc
    # enact trade logic
