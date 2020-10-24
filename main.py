import time
from datetime import datetime, timedelta
import pandas as pd
from naver_finance_day_sise import *

codes = []
kospi_codes = pd.read_csv('./kospi_201024.csv')
for code in kospi_codes['종목코드']:
    codes.append('{0:06d}'.format(code))
start = datetime(2020, 10, 18)
end = datetime(2020, 10, 24)

# exportStockData(codes, start, end)

interest_stock_list = []
for code in codes:
    if getGigwanBuy(code, 5, 4) or getFrgnBuy(code, 5, 4):
        interest_stock_list.append(code)

for code in interest_stock_list:
    print(code)