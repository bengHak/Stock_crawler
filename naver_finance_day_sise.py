import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta


def exportPriceData(code, startdate, enddate):
    isEnd = False
    res = {
        'index': [],
        'data': []
    }

    page = 1
    while isEnd != True:
        url = "https://finance.naver.com/item/sise_day.nhn?code=" + code + "&page=" + str(page)
        response = requests.get(url)
        html = bs(response.text, 'html.parser')

        # parse
        trList = html.find_all("tr", {"onmouseover": "mouseOver(this)"})
        for tr in trList:
            tdList = tr.find_all('td')
            # print(tdList[0].text.strip())  # 날짜
            # print(tdList[1].text.strip())  # 종가
            # print(tdList[2].text.strip())  # 전일비
            # print(tdList[3].text.strip())  # 시가
            # print(tdList[4].text.strip())  # 고가
            # print(tdList[5].text.strip())  # 저가
            # print(tdList[6].text.strip())  # 거래량

            date = tdList[0].text.strip()  # 날짜
            if date == '':
                isEnd = True
                break
            closePrice = int(tdList[1].text.strip().replace(',', ''))  # 종가
            diffPrice = int(tdList[2].text.strip().replace(',', ''))  # 전일비
            openPrice = int(tdList[3].text.strip().replace(',', ''))  # 시가
            highPrice = int(tdList[4].text.strip().replace(',', ''))  # 고가
            lowPrice = int(tdList[5].text.strip().replace(',', ''))  # 저가
            volume = int(tdList[6].text.strip().replace(',', ''))  # 거래량

            target = datetime.strptime(date.replace('.', '-'), '%Y-%m-%d')
            if target < startdate:
                isEnd = True
                break
            elif target < enddate and target > startdate:
                # print(target)
                # insert index
                res['index'].insert(0, date)

                # insert data with ["High","Low","Open","Close","Volume","Adj Close"]
                res['data'].insert(0, [highPrice, lowPrice, openPrice, closePrice, volume])

        page += 1
        # time.sleep(2)

    path = f'./data/{code}/'
    if not os.path.isdir(path):
        os.mkdir(path)

    df = pd.DataFrame(data=res['data'], index=res['index'])
    df.to_json(path + code + '_price.json', orient='split', date_format='index')

def exportTransactionVolume(code, startdate, enddate):
    isEnd = False
    res = {
        'index': [],
        'data': []
    }
    page = 1

    while isEnd != True:
        url = 'http://finance.naver.com/item/frgn.nhn?code=' + code + '&page=' + str(page)
        html = requests.get(url)
        source = bs(html.text, "html.parser")
        dataSection = source.find("table", summary="외국인 기관 순매매 거래량에 관한표이며 날짜별로 정보를 제공합니다.")
        dayDataList = dataSection.find_all("tr")

        for i in range(3, len(dayDataList)):
            if (len(dayDataList[i].find_all("td", class_="tc")) != 0 and len(dayDataList[i].find_all("td", class_="num")) != 0):
                day = dayDataList[i].find_all("td", class_="tc")[0].text.strip()
                if day == '':
                    isEnd = True
                    break
                institutionPureDealing = int(dayDataList[i].find_all("td", class_="num")[4].text.strip().replace(',',''))
                foreignerPureDealing = int(dayDataList[i].find_all("td", class_="num")[5].text.strip().replace(',',''))
                ownedVolumeByForeigner = int(dayDataList[i].find_all("td", class_="num")[6].text.strip().replace(',',''))
                ownedRateByForeigner = float(dayDataList[i].find_all("td", class_="num")[7].text.strip().replace(',','').replace('%',''))
                # print("날짜: " + day, end=" ")
                # print("기관순매매: " + institutionPureDealing, end=" ")
                # print("외인순매매: " + foreignerPureDealing, end=" ")
                # print("외인보유 주식수: " + ownedVolumeByForeigner, end=" ")
                # print("외인 보유율: " + ownedRateByForeigner)

                target = datetime.strptime(day.replace('.', '-'), '%Y-%m-%d')
                if target < startdate:
                    isEnd = True
                    break
                elif target < enddate and target > startdate:
                    # print(target)
                    # insert index
                    res['index'].insert(0, day)
                    res['data'].insert(0, [institutionPureDealing, foreignerPureDealing, ownedVolumeByForeigner, ownedRateByForeigner])
    path = f'./data/{code}/'
    if not os.path.isdir(path):
        os.mkdir(path)

    df = pd.DataFrame(data=res['data'], index=res['index'])
    df.to_json(path + code + '_transaction.json', orient='split', date_format='index')

def exportStockData(codes, start, end):
    codes_len = len(codes)
    idx = 1
    for code in codes:
        codeStartTime = time.time()
        exportPriceData(code, start, end)
        exportTransactionVolume(code, start, end)
        estimatedTime = str(timedelta(seconds=((time.time() - codeStartTime) * (codes_len - idx)))).split('.')[0]
        print(f'{code} Completed | Estimated time: {estimatedTime} |({idx}/{codes_len})')
        idx += 1

    print('Export Complete!')
    return

def getGigwanBuy(code, duration, buyDay):
    file_path = f'./data/{code}/{code}_transaction.json'
    if not os.path.exists(file_path):
        return False

    with open(file_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame.from_dict(data, orient='index')
    # print(df.T['data'][-1*duration:])

    recent5days = df.T['data'][-1*duration:]
    buy_count = 0
    for val in recent5days:
        if val[0] > 0:
            buy_count += 1

    if buy_count >= buyDay:
        return True
    return False

def getFrgnBuy(code, duration, buyDay):
    file_path = f'./data/{code}/{code}_transaction.json'
    if not os.path.exists(file_path):
        return False

    with open(file_path, 'r') as f:
        data = json.load(f)

    df = pd.DataFrame.from_dict(data, orient='index')
    # print(df.T['data'][-1*duration:])

    recent5days = df.T['data'][-1*duration:]
    buy_count = 0
    for val in recent5days:
        if val[1] > 0:
            buy_count += 1

    if buy_count >= buyDay:
        return True
    return False

    return True