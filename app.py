import yfinance as yf
from pprint import pprint

data = yf.Ticker('AMZN')
#pprint(data.info)
#print(data.calendar)
#print(data.analyst_price_targets)
#print(data.quarterly_balancesheet)
#print(data.income_stmt)
#print(data.history(period='1mo'))
pprint(data.option_chain(data.options[0]).calls)