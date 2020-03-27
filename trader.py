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



#NOTES
#maybe remove sell stock loop from SMA check? as with update?
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
        self.capital = 1060.2123
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
        data = {}
        try:
            response = requests.get(self.API_URL, SMA_high)
            data = response.json()
            a = data['Technical Analysis: SMA']
            keys = a.keys()
            newest_key = list(keys)[0]
            symbol["SMA"] = float(a[newest_key]["SMA"])
            return symbol
        except Exception as e:
            print("Error getting SMA of {}, {}".format(symbol['symbol'],data['Error Message']))
            symbol["SMA"] = 2**1000
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
        Current_Price = { "function": "TIME_SERIES_INTRADAY",
        "symbol": symbol['symbol'],
        "interval" : "1min",
        "datatype": "json",
        "apikey": os.getenv("API_KEY") }
        data = {}
        try:
            response = requests.get(self.API_URL, Current_Price)
            data = response.json()
            a = (data['Time Series (1min)'])
            keys = (a.keys())
            newest_key = list(keys)[0]
            #print(str(a[newest_key]))
            symbol["Current_Price"] = float(a[newest_key]["1. open"])
            return symbol
        except Exception as e:
            try:
                print("Error getting Current price of {}, {}".format(symbol['symbol'], data['Error Message']))
                print("Setting current price to last price found...")
                symbol["Current_Price"] = symbol["Last_Price"]
            except:
                print("No last price found... setting to -100")
                symbol["Current_Price"] = -100
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
    def buy_stock(self, symbol, current_assets):
        self.bought_stocks.append(symbol['symbol'])
        num_shares = self.capital * self.risk / symbol['Current_Price']
        print("Bought {} shares of {}".format(num_shares,symbol['symbol']))
        print("\nBuying {} @ {} per share".format(symbol["symbol"], symbol["Current_Price"]))
        symbol["Shares_Bought"] = num_shares
        symbol["Last_Price"] = symbol["Current_Price"]
        symbol["Bought_Price"] = symbol["Current_Price"]
        symbol["Exit"] = symbol["Current_Price"] * .97
        print("Setting exit @ {}\n".format(symbol["Exit"]))
        self.capital -= (symbol["Shares_Bought"] * symbol["Current_Price"])
        current_assets = current_assets + (symbol["Shares_Bought"] * symbol["Current_Price"])
        print("Current account balance: {}\n".format(self.capital))

        return symbol, current_assets
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
    def sell_stock(self, symbol, current_assets):
        print("\nSold {} @ {}".format(symbol['symbol'], symbol['Current_Price']))
        self.capital += (symbol["Shares_Bought"] * symbol["Current_Price"])
        current_assets = current_assets - (symbol["Shares_Bought"] * symbol["Current_Price"])
        print("Current account balance: {}\n".format(self.capital))
        change = (symbol["Shares_Bought"] * symbol["Current_Price"]) - (symbol["Shares_Bought"] * symbol["Bought_Price"])
        if change > 0:
            print("Sold all of {} for {} in profit!".format(symbol['symbol'], change))
        else:
            print("Sold all of {} for a {} loss!".format(symbol['symbol'], change))
        return current_assets

    def update_stock(self, symbol, current_assets):
        current_assets = current_assets - (symbol["Shares_Bought"] * symbol["Last_Price"])
        current_assets = current_assets + (symbol["Shares_Bought"] * symbol["Current_Price"])
        symbol["Last_Price"] = symbol["Current_Price"]
        symbol["Exit"] = symbol["Current_Price"] * .97
        print("\n{} rose to {}, updating exit to {}\n".format(symbol['symbol'], symbol['Current_Price'], symbol['Exit']))
        return symbol, current_assets

"""
    Author: Ryan Davis
    Date: 3/23/2020

    Scapes yahoo finance gainers for the first page of the most changed stocks today, only

    Arguments:
        None
    Returns:
        stocks_to_watch: array of of stocks, each containing symbol, price, change, volume
"""
def get_stocks_to_watch(searched_stocks):
    stocks_to_watch = []

    driver = webdriver.Chrome()
    driver.set_window_position(-2000,0)
    driver.get("http://finance.yahoo.com/gainers")

    elem = driver.find_element_by_name
    table = driver.find_element_by_xpath("//table[@class='W(100%)']/tbody")
    row = table.find_element_by_xpath(".//tr[@class='simpTblRow Bgc($extraLightBlue):h BdB Bdbc($finLightGrayAlt) Bdbc($tableBorderBlue):h H(32px) Bgc(white) ']")
    while row:
        symbol = row.find_element_by_xpath(".//td[1]").text
        price = row.find_element_by_xpath(".//td[3]").text
        change = row.find_element_by_xpath(".//td[5]").text
        volume = row.find_element_by_xpath(".//td[6]").text
        print(symbol, price, change, volume)
        if symbol not in searched_stocks:
            if "M" in volume and "+" in change:
                stock = {"symbol":symbol, "price":price,"change":change, "volume":volume}
                stocks_to_watch.append(stock)
        try:
            row = row.find_element_by_xpath(".//following-sibling::tr")
        except:
            print("no more rows!\n")
            return stocks_to_watch
"""
    Author: Ryan Davis
    Date: 3/26/2020

    Waits until next trading day. Doesnt currently account for weekends but oh well.

    Arguments:
        None
    Returns:
        None
"""
def wait_until_next_day():
    print("waiting")
    now = datetime.datetime.today()
    future = datetime.datetime(now.year,now.month,now.day,9,30)
    if (now.weekday() == 5): # five refers to saturday here
        future += datetime.timedelta(days=2)
    elif (now.weekday() == 6): #six refers to sunday
        future += datetime.timedelta(days=1)
    elif(now.hour > 16): # if its past four PM, just move to the next day.
        future += datetime.timedelta(days=1)
        if future.weekday==5: # accounts for case that its friday past 4pm. wait until monday
            future += datetime.timedelta(days=2)
    print((future-now).seconds)
    time.sleep((future-now).seconds)

def reset(total_assets, symbols):
    stocks_to_watch = []
    return total_assets, stocks_to_watch, symbols

def print_account_holdings(symbols):
    print("Current account summary: \n\tAssets: {} \n\tCash: {} \n\tTotal: {} \n\tgains/losses: {}\n".format(current_assets, trader.capital, current_assets + trader.capital, (current_assets + trader.capital) - start_balance))
    print("Current Holdings: ")
    for symbol in symbols:
        print("{} shares of {}".format(symbol["Shares_Bought"], symbol["symbol"]))
    print()



if __name__ == "__main__":
    trader = Stock_Trader()
    stocks_to_remove = []
    searched_stocks = []
    num_stocks = 0
    count = 0
    current_assets = 0
    start_balance = trader.capital
    stocks_to_watch = get_stocks_to_watch(trader.bought_stocks)
    trader.symbols = stocks_to_watch[:5]

    for symbol in trader.symbols:
        symbol = trader.getSMAhigh(symbol)
        print(symbol)

    time.sleep(60)
    trading = True
    while trading:
        total_assets = trader.capital + current_assets
        if total_assets < start_balance * .985:
            print("quitting for the day, too many losses")
            for symbol in trader.symbol:
                if symbol['symbol'] in trader.bought_stocks:
                    num_stocks -= 1
                    current_assets = trader.sell_stock(symbol, current_assets)
                    stocks_to_remove.append(symbol)
            wait_until_next_day()
            start_balance = total_assets
            stocks_to_remove = []
            searched_stocks = symbols

        now = datetime.datetime.now()
        today930 = now.replace(hour=9, minute=30, second=0, microsecond=0)
        today4 = now.replace(hour=16, minute=0, second=0, microsecond=0)
        today345 = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if now > today345:
            for symbol in trader.symbols:
                num_stocks -= 1
                symbol, current_assets = trader.sell_stock(symbol, current_assets)
                stocks_to_remove.append(symbol)
            wait_until_next_day()
            start_balance, stocks_to_remove, searched_stocks = reset(total_assets, trader.symbols)

        if now < today930 or now > today4:
            print("not in trading hours... sleeping")
            wait_until_next_day()
            start_balance, stocks_to_remove, searched_stocks = reset(total_assets, trader.symbols)

        for symbol in trader.symbols:
            symbol = trader.getCurrentPrice(symbol)
            searched_stocks.append(symbol['symbol'])
            if symbol["Current_Price"] > symbol["SMA"]:
                if symbol["symbol"] not in trader.bought_stocks:
                    num_stocks += 1
                    symbol, current_assets = trader.buy_stock(symbol, current_assets)

                if symbol["Current_Price"] > symbol["Last_Price"]:
                    symbol, current_assets = trader.update_stock(symbol, current_assets)

                if symbol["Current_Price"] <= symbol["Exit"]:
                    num_stocks -= 1
                    current_assets = trader.sell_stock(symbol, current_assets)
                    stocks_to_remove.append(symbol)
            else:
                stocks_to_remove.append(symbol)
                print("{} price was not above SMA, abandoning...".format(symbol['symbol']))
                #accounts for the case that the stock value drops rapidly below SMA when it was previously above
                #or accounts for case that stock value is just above SMA then falls just below
                if symbol['symbol'] in trader.bought_stocks:
                    num_stocks -= 1
                    current_assets = trader.sell_stock(symbol, current_assets)
                    stocks_to_remove.append(symbol)
        for stock in stocks_to_remove:
            trader.symbols.remove(stock)
        if count % 2 == 0:
            print_account_holdings(trader.symbols)
        count += 1

        if len(trader.symbols) < 5:
            #repeat the process
            print("Searching for new stocks")
            stocks_to_remove = []
            new_stocks = get_stocks_to_watch(searched_stocks)
            if len(new_stocks) == 0 and len(trader.symbols) == 0:
                print("no new stocks found... will try again tomorrow")
                wait_until_next_day()
                start_balance, stocks_to_remove, searched_stocks = reset(total_assets, trader.symbols)
            new_stock_ct = 0
            while len(trader.symbols) != 5 and len(new_stocks) != 0:
                try:
                    trader.symbols.append(new_stocks[new_stock_ct])
                except Exception as e:
                    print("No more new stocks... breaking loop")
                    break
                new_stock_ct += 1
            time.sleep(60)
            for symbol in trader.symbols:
                try:
                    if symbol['SMA'] > 0:
                        continue
                except:
                    symbol = trader.getSMAhigh(symbol)
        time.sleep(60)
