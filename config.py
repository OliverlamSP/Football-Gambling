import time
import requests
# from sqlalchemy import create_engine

get = 'get'
post = 'post'

no_of_trials = 20
sleeptime = 5

# schema_file = 'db_schema.xlsx'
# schema_sheet = 'Sheet1'
# db = 'postgres'
# user = 'postgres'
# pw = 'sevenparadise7'
# database_name = 'postgres'
# engine = create_engine('postgresql://{0}:{1}@localhost:5432/{2}'.format(user,pw,database_name))

# Headers of win007 website
headers_win007 = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.110 Safari/537.36',
            'Referer': 'http://zq.win007.com/big/League/2017-2018/36.html'}

header_win007_leagueID = {
    # 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    # 'Accept-Encoding': 'gzip, deflate',
    # 'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    # 'Cache-Control': 'max-age=0',
    # 'Connection': 'keep-alive',
    # 'Cookie': 'UM_distinctid=163a0547d796f2-07d0d966f16395-b353461-144000-163a0547d7a470; CNZZDATA1261430177=1343602463-1527401439-%7C1542528192',
    # 'Host': 'zq.win007.com',
    'Referer': 'http://www.win007.com/',
    # 'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.102 Safari/537.36'
    }
    

# Testing path (Yahoo)
path_yahoo = 'https://hk.yahoo.com/'
# Testing path (win007)
path_win007 = 'http://zq.win007.com/cn/League/2018-2019/36.html'

path_win007_leagueID = 'http://zq.win007.com/jsData/infoHeader.js'

"""
Input Value Area:

Arg below are going to be used as arg in scrapping.py
"""

# The scrapping  method that is going to be used
method = get

# Store the URL of the requesting website into String url, here can change the
# url value to adjust the url
url = path_win007_leagueID

# Headers that will be used in scrapping
headers = header_win007_leagueID

# Retry the URL
