import requests
from datetime import datetime
from random import randint
import config
import utilities
import pandas as pd
import re
import ast
import time 
import numpy as np
from bs4 import BeautifulSoup
import tqdm

def getpostdata(request_method, url, no_of_trials=config.no_of_trials,
                header=None, sleeptime=config.sleeptime):
    """
    getpostdata function is used to get the content of a website upon
    a given url.

    Parameters
    ----------
    request_method : String
        The request method would like to use.
        'get' : use get method
        'post' : use post method
    url : String
        The url would like to scrap.
    no_of_trials : int
        The maximum number of trials that we want to scrap under the single run
        of the programme.
    header : Dictionary of {String: String} (Optional, default = None)
        The request header of the website.
    sleeptime : int
        The maximum length of sleep time would like to apply (second).
        Sleep time is a random number starting from 2 seconds.

    Returns
    -------
    Requests Response Object
        The response from requesting the specified URL.

    """    
    # Try the number of time of trials and get the response from the url
    for _ in range(no_of_trials):
        try:
            # Run the requests by using the input method(request_method)
            if request_method == 'get':
                return requests.get(url, headers=header)
            elif request_method == 'post':
                return requests.post(url, headers=header)
            else:
                raise AttributeError(
                    "request_method must be \'get\' or \'post\'")
        # As long as there is an error, the programme will sleep for the
        # defined time.
        # Without header will cause ConnectionError Exception.
        except Exception as e:
            print(e)
            time.sleep(10)

    raise ConnectionError("Unable to {} {}".format(request_method, url))

# ------- WIN007 -----------------

def win007__getpostdata(request_method, url, referer=None):
    
    header = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"
    }
    header['Referer'] = referer
    return getpostdata(request_method, url, header=header)

def win007__get_league_id_and_season_list():
    """
    win007__get_league_id_and_season_list function is used to get a list of 
    league_id_and_season_list

    Returns
    -------
        return a list of league_id_and_season_list

    """    
    # Define constants
    REQUEST_METHOD = 'get'
    URL = 'http://zq.win007.com/jsData/infoHeader.js'
    REFERER = 'http://zq.win007.com/cn/League/36.html'
    FULL_LEAGUE_ID_PATTERN = "arr\[\d+\] = \[[^\[]+\[([^;]+)\]\];"
    INDIVIDUAL_LEAGUE_ID_PATTERN = r'[^"]{2,}'

    # Request league id/season list page
    res = win007__getpostdata(REQUEST_METHOD, URL, REFERER)

    # Parse page
    # --- full league & season list
    league_id_string = res.text
    league_id_list = utilities.pattern_findall(
        FULL_LEAGUE_ID_PATTERN, league_id_string)
    
    # --- individual league & season list
    all_league_id_list = []
    for league in range(len(league_id_list)):
        league_id_list_individual = utilities.pattern_findall(
            INDIVIDUAL_LEAGUE_ID_PATTERN, league_id_list[league])
        for number in range(len(league_id_list_individual)):
            all_league_id_list.append(
                league_id_list_individual[number].split(','))
    time.sleep(config.sleeptime)
    return all_league_id_list


def win007__get_league_id():
    """
    win007__get_league_id function is used to get a list of 
    all league_id

    Returns
    -------
        return a list of all league_id
    """    
    league_id_list = []
    sub_league_id_list = []
    no_sub_league_id_list = []
    all_list = []
    all_league_id_list = win007__get_league_id_and_season_list()
    for length in range(len(all_league_id_list)):
        league_id_list.append(all_league_id_list[length][0:4])
        
    for league in range(len(all_league_id_list)):
        all_list.append(all_league_id_list[league][0])
        if all_league_id_list[league][3] == '1':
            sub_league_id_list.append(all_league_id_list[league][0])
    time.sleep(config.sleeptime)
    return all_list,sub_league_id_list

def win007__get_subleague_id():
    """
    win007__get_subleague_id function is used to get a list of 
    all sub_league_id
    """
    all_list,sub_league_id_list = win007__get_league_id()
    SUB_LEAGUE_ID_PATTERN = 'SubSclassID = (\d+);'
    all_sub_league_id_dict ={}
    for league_id in sub_league_id_list:
        REQUEST_METHOD = 'get'
        URL = 'http://zq.win007.com/cn/SubLeague/2018-2019/{}.html'.format(league_id)
        REFERER = 'http://zq.win007.com/cn/SubLeague/2018-2019/23.html'
        res = win007__getpostdata(REQUEST_METHOD, URL, REFERER)
        sub_league_id_string = res.text
        sub_league_id = utilities.pattern_findall(
        SUB_LEAGUE_ID_PATTERN, sub_league_id_string)
        if len(sub_league_id) > 0:
             sub_league_id = utilities.pattern_findall(SUB_LEAGUE_ID_PATTERN, sub_league_id_string)[0]
        else: continue
        all_sub_league_id_dict[league_id] = sub_league_id
    time.sleep(config.sleeptime)
    return all_sub_league_id_dict

def win007__get_season_list():
    """
    win007__get_season_list function is used to get a list of 
    all season

    Returns
    -------
        return a list of all season
    """    
    LEAGUE_ID_IDX = 0
    LEAGUE_NAME_IDX = 1
    
    season_dict = {}
    all_league_id_list = win007__get_league_id_and_season_list()
    for league in all_league_id_list:
        season_dict[league[LEAGUE_ID_IDX]] = [item for item in league if '-' in item]
    time.sleep(config.sleeptime)
    return season_dict


def win007__get_match_detail(league_id):
    """
    get_match_detail function is used to get the match detail of a league

    Parameters
    ----------
    league_id : string
        input league_id in get_match_detail function and get match_detail

    Returns
    -------
    DataFrame
        A dataframe with match detali of all season of a league

    """    
    match_result_df = pd.DataFrame()
    present = datetime.now()
    REQUEST_METHOD = 'get'
    season_dict = win007__get_season_list()
    season_string_list = season_dict.get(league_id)
    all_sub_league_id_dict = win007__get_subleague_id()
    sub_league_id = all_sub_league_id_dict.get(league_id)
    _list = ['26','22','4','21','415','25','284','15']
    if league_id in _list:
        # season_string_list = ['2019']
        season_string_list = ['2019','2018','2017','2016','2015','2014','2013','2012','2011','2010','2009','2008','2007','2006','2005','2004','2003']
    if league_id == '16':
        sub_league_id = '98'
    if league_id == '23':
        sub_league_id = '1123'
    if league_id == '17':
        sub_league_id = '94'
    if league_id == '5':
        sub_league_id = '114'
    if league_id == '2':
        sub_league_id = '1232'
    if league_id == '35':
        sub_league_id = '139'
    if league_id == '37':
        sub_league_id = '87'
    if league_id == '39':
        sub_league_id = '135'
    if league_id == '26':
        sub_league_id = '431'
    if league_id == '21':
        sub_league_id = '165'
    if league_id == '415':
        sub_league_id = '395'
    if league_id == '25':
        sub_league_id = '943'
    if league_id == '284':
        sub_league_id = '808'
    if league_id == '273':
        sub_league_id = '462'
    if league_id == '15':
        sub_league_id = '313'
    if league_id == '14040':
        league_id = '140' 
        sub_league_id = '40'
    if league_id == '14044':
        league_id = '140' 
        sub_league_id = '44'
    
    if league_id == '140':
        season_string_list = ['2018-2019','2017-2018','2016-2017','2015','2014','2013','2012','2011','2010','2009','2008','2007','2006','2005']
    
    if league_id == '2':
        season_string_list = ['2016','2015','2014']

    if league_id == '224':
        league_id = '2'
        sub_league_id = '24'
        season_string_list = ['2013-2014','2012-2013','2011-2012','2010-2011','2009-2010','2008-2009','2007-2008','2006-2007','2005-2006','2004-2005']
    if league_id == '225':
        league_id = '2'
        sub_league_id = '24'
        season_string_list = ['2013-2014','2012-2013','2011-2012','2010-2011','2009-2010','2008-2009','2007-2008','2006-2007','2005-2006','2004-2005']
    COLUMNS_1_TRIAL = ['Match_id','League_id','Skip0','Date_Time','Home_Team_id','Away_Team_id','FT_Result','HT_Result','Previous_Round_Home_Team_Ranking','Previous_Round_Away_Team_Ranking',
                                    'FT_Home_Team_Asian_Handicap_Median','HT_Home_Team_Asian_Handicap_Median','FT_Big_Small_Median','HT_Big_Small_Median','Skip1','Skip2','Skip3','Skip4','Home_Red_Card','Away_Red_Card'
                                    ,'Skip5','Skip6','Skip7','week']
    COLUMNS_2_TRIAL = ['Match_id','League_id','Skip0','Date_Time','Home_Team_id','Away_Team_id','FT_Result','HT_Result','Previous_Round_Home_Team_Ranking','Previous_Round_Away_Team_Ranking',
                        'FT_Big_Small_Median','HT_Big_Small_Median','Skip1','Skip2','Skip3','Skip4','Home_Red_Card','Away_Red_Card'
                            ,'Skip5','Skip6','Skip7','week']

    for season in tqdm.tqdm(season_string_list):
        time.sleep(config.sleeptime)
        REFERER = 'http://zq.win007.com/big/League/{0}/{1}.html'.format(season,league_id)
        if league_id == '140':
            if sub_league_id == '40':
                REFERER = 'http://zq.win007.com/big/SubLeague/{0}/{1}_{2}.html'.format(season,league_id,sub_league_id)
            if sub_league_id == '44':
                REFERER = 'http://zq.win007.com/big/SubLeague/{0}/{1}_{2}.html'.format(season,league_id,sub_league_id)
        if sub_league_id is None or len(sub_league_id) == 0:
            URL = 'http://zq.win007.com/jsData/matchResult/{0}/s{1}.js?version={2}'.format(season,league_id,present.strftime('%Y%m%d%H'))
        else:
            URL = 'http://zq.win007.com/jsData/matchResult/{0}/s{1}_{2}.js?version={3}'.format(season,league_id,sub_league_id,present.strftime('%Y%m%d%H'))  
        res = win007__getpostdata(REQUEST_METHOD, URL,REFERER)
        if res.text == '404 Not Found !':
            print('nothing found')
            continue
        season_result_list = utilities.pattern_findall("jh\[\"R_\d{1,3}\"\] = ([^;]+);",res.text)
        season_result_df = pd.DataFrame()
        for i,week in enumerate(season_result_list):
            try:
                week = re.sub(',,',',\'\',',week)
                week = re.sub(',,',',\'\',',week)
                week_result_list = ast.literal_eval(week)
            except:
                print(week)
                assert 0
            week_result_df = pd.DataFrame(week_result_list)
            week_result_df['week'] = i+1
            season_result_df = season_result_df.append(week_result_df)
        try:
            season_result_df.columns = COLUMNS_1_TRIAL
        except:
            try:
                season_result_df.columns = COLUMNS_2_TRIAL
            except:
                assert 0
        season_result_df['season'] = season
        match_result_df = match_result_df.append(season_result_df)

    df = match_result_df[[col for col in match_result_df.columns if not col.startswith('Skip')]]
    # trial_on_db.insert_data('win007_match_detail',df)
    return df
def get_combination_sets(df):
    if df.empty:
        return set()
    else:
        return set(df[['company_id' ,'match_id']].drop_duplicates().apply(lambda x: (x['company_id'], x['match_id']), 1).tolist())

def get_asian_odd_change(league_id,df_asian_not_exist,df_asian_odd_change,to_crawl_list):
    '''NEED CREATE TABLE ASIAN_NOT_EXIST'''
    """
    get_odd_change function is used to get odd change 

    Parameters
    ----------
    df_odd_change : DataFrame
        storing odd change, get from database

    df_asian_not_exist : DataFrame
        storing match_id and company_id which do not have odd change, get from database

    -------
    Directly store into database

    """    
    columns = ['company_id','match_id','bet_option','odd','median','date_time','status']
    for match_id in tqdm.tqdm(to_crawl_list): 
        company_id = '12'
        METHOD = 'get'
        URL = 'http://vip.win007.com/changeDetail/handicap.aspx?id={0}&companyID={1}'.format(match_id,company_id)
        REFERER = 'http://vip.bet007.com/changeDetail/1x2.aspx?id={0}&companyid={1}&l=0'.format(match_id,company_id)
        res = win007__getpostdata(METHOD,URL,REFERER)
        if res is None:

            df1 = pd.DataFrame([[company_id,match_id]],columns = ['company_id' ,'match_id'])
            # trial_on_db.insert_data('win007_asian_not_exist',df1)
            df_asian_not_exist = df_asian_not_exist.append(df1)
            df_asian_not_exist.to_csv('win007_asian_not_exist.csv',encoding = 'utf8',index = False)
            continue
        try:
            data = res.content
            soup = BeautifulSoup(data,'html.parser')
            odd = soup.find('span', id='odds2')
            row = odd.find_all('tr')
            match_odd_change_data = []
            for rows in row[1:]:
                box = rows.find_all('td')
                box = [i.text for i in box]
                home_team_odds = box[0]
                median = box[1]
                away_team_odds = box[2]
                date_time = box[3]
                status = box[4]

                box = [[company_id,match_id, 'Home', home_team_odds, median, date_time, status],
                    [company_id,match_id, 'Away', away_team_odds, median, date_time, status]]
                match_odd_change_data.extend(box)
                
            if len(match_odd_change_data) == 0:
                df1 = pd.DataFrame([[company_id,match_id]],columns = ['company_id' ,'match_id'])
                # trial_on_db.insert_data('win007_asian_not_exist',df1)
                df_asian_not_exist = df_asian_not_exist.append(df1)
                df_asian_not_exist.to_csv('win007_asian_not_exist.csv',encoding = 'utf8',index = False)
                continue

            df = pd.DataFrame(match_odd_change_data,columns = columns)
            # trial_on_db.insert_data('win007_asian_odd_change',df)
            df_asian_odd_change = df_asian_odd_change.append(df)
        except:
            df1 = pd.DataFrame([[company_id,match_id]],columns = ['company_id' ,'match_id'])
            # trial_on_db.insert_data('win007_asian_not_exist',df1)
            df_asian_not_exist = df_asian_not_exist.append(df1)
            df_asian_not_exist.to_csv('win007_asian_not_exist.csv',encoding = 'utf8',index = False)
            continue
    df_asian_odd_change.to_csv('win007_asian_odd_change_{}.csv'.format(league_id),encoding = 'utf8',index = False)

def win007__asian_odd_change(league_id):
    'Need change name of database table from win007_odd_change to win007_europena_odd_change'
    print(league_id)
    # df = trial_on_db.read_data_as_dataframe('win007_match_detail')
    df = pd.read_csv('win007_match_detail.csv')
    df = df[df['League_id'] == league_id]
    df = df[df['FT_Result']!='']
    match_id_list = df['Match_id'].unique() 
    company_id_list = ['12']
    # df_asian_odd_change = pd.read_csv('win007_asian_odd_change.csv')
    # df_asian_odd_change = trial_on_db.read_data_as_dataframe('win007_asian_odd_change')
    df_asian_not_exist = pd.read_csv('win007_asian_not_exist.csv')
    # df_asian_not_exist = trial_on_db.read_data_as_dataframe('win007_asian_not_exist')

    # all_list = set([(company_id, match_id) for match_id in match_id_list for company_id in company_id_list])
    # crawled_list = get_combination_sets(df_asian_odd_change)
    # not_exist_list = get_combination_sets(df_asian_not_exist)
    # to_crawl_list = list(all_list - crawled_list - not_exist_list)
    # to_crawl_list.sort(key=lambda tup: tup[1],reverse=True)
    to_crawl_list = match_id_list
    df_asian_odd_change = pd.DataFrame()
    print(len(to_crawl_list))
    get_asian_odd_change(league_id,df_asian_not_exist,df_asian_odd_change,to_crawl_list)

def get_european_odd_change(to_crawl_list):

    for company_id, match_id in tqdm.tqdm(to_crawl_list):
        METHOD = 'get'
        URL = 'http://vip.win007.com/changeDetail/1x2.aspx?id={0}&companyid={1}&l=0'.format(match_id,company_id)
        REFERER = 'http://vip.bet007.com/changeDetail/handicap.aspx?id={0}&companyID={1}'.format(match_id,company_id)
        column = ['company_id','match_id','bet_option','odd','date_time','status']
        res = win007__getpostdata(METHOD,URL,REFERER)
        if res is None:
            df1 = pd.DataFrame([[company_id,match_id]],columns = ['company_id' ,'match_id'])
            # trial_on_db.insert_data('win007_european_not_exist',df1)
            continue
        data = res.content
        soup = BeautifulSoup(data,'html.parser')
        row = soup.find_all('tr')
        match_odd_change_data = []

        for rows in row[1:]:
            box = rows.find_all('td')
            box = [i.text for i in box]
            home_team_odds = box[0]
            draw_odds = box[1]
            away_team_odds = box[2]
            date_time = box[3]
            status = box[4]

            box = [[company_id,match_id,'Home',home_team_odds,date_time,status],
                    [company_id,match_id,'Draw',draw_odds,date_time,status],
                    [company_id,match_id,'Away',away_team_odds,date_time,status]]

            match_odd_change_data.extend(box)

        if len(match_odd_change_data) == 0:
            df1 = pd.DataFrame([[company_id,match_id]],columns = ['company_id' ,'match_id'])
            # trial_on_db.insert_data('win007_european_not_exist',df1)
            continue

        df = pd.DataFrame(match_odd_change_data,columns = column)
        # trial_on_db.insert_data('win007_european_odd_change',df)

def win007__european_odd_change():
    # df = trial_on_db.read_data_as_dataframe('win007_match_detail')
    df = df[df['FT_Result']!='']
    match_id_list = df['Match_id'].unique() 
    company_id_list = ['1','12']
    # df_european_odd_change = trial_on_db.read_data_as_dataframe('win007_european_odd_change')
    # df_european_not_exist = trial_on_db.read_data_as_dataframe('win007_european_not_exist')
    all_list = set([(company_id, match_id) for match_id in match_id_list for company_id in company_id_list])
    crawled_list = get_combination_sets(df_european_odd_change)
    not_exist_list = get_combination_sets(df_european_not_exist)
    to_crawl_list = list(all_list - crawled_list - not_exist_list)
    # to_crawl_list.sort(key=lambda tup: tup[1],reverse=True)
    get_european_odd_change(to_crawl_list)


def win007__get_team_id(league_id):
    """
    get_team_id function is used to get team_in and team_name 

    Parameters
    ----------
    League_id

    -------
    Directly store into database

    """    
    season_dict = win007__get_season_list()
    season_string_list = season_dict.get(league_id)
    all_sub_league_id_dict = win007__get_subleague_id()
    sub_league_id = all_sub_league_id_dict.get(league_id)
    _list = ['26','22','4','21','415','25','284','15']
    if league_id in _list:
        season_string_list = ['2018','2017','2016','2015','2014','2013','2012','2011','2010','2009','2008','2007','2006','2005','2004','2003']
    # sub_dict = {'23':'1123','2','1232','16':'98','17':'94','5':'114','26','431','21':'165','415':'395','25':'943','284':'808','273':'462','15':'313'}
    present = datetime.now()
    df_team_id = pd.DataFrame()
    # sub_league_id = sub_dict.get(league_id)
    for season in tqdm.tqdm(season_string_list):
        REQUEST_METHOD = 'get'

        if league_id == '23':
            sub_league_id = '1123'
        if league_id == '10':
            sub_league_id = '591'
        if league_id == '2':
            sub_league_id = '1232'
        if league_id == '16':
            sub_league_id = '98'
        if league_id == '17':
            sub_league_id = '94'
        if league_id == '5':
            sub_league_id = '114'    
        if league_id =='26':
            sub_league_id = '431'
        if league_id == '21':
            sub_league_id = '165'
        if league_id == '415':
            sub_league_id = '395'
        if league_id == '25':
            sub_league_id = '943'
        if league_id == '284':
            sub_league_id = '808'
        if league_id == '273':
            sub_league_id = '462'
        if league_id == '15':
            sub_league_id = '313'
        REFERER = 'http://zq.win007.com/big/League/{0}/{1}.html'.format(season,league_id)
        if sub_league_id is None or len(sub_league_id) == 0:
            URL = 'http://zq.win007.com/jsData/matchResult/{0}/s{1}.js?version={2}'.format(season,league_id,present.strftime('%Y%m%d%H'))
        else:
            URL = 'http://zq.win007.com/jsData/matchResult/{0}/s{1}_{2}.js?version={3}'.format(season,league_id,sub_league_id,present.strftime('%Y%m%d%H'))  
        time.sleep(3)
        res = win007__getpostdata(REQUEST_METHOD, URL,REFERER)
        if res.text == '404 Not Found !':
            continue
            
        season_result_string = res.text
        team_id_pattern = re.compile("var arrTeam = ([^;]+);")
        team_name_id_source = team_id_pattern.findall(season_result_string)
        team_name_id_string = re.sub(' +',' ',team_name_id_source[0])
        team_name_id_list = ast.literal_eval(team_name_id_string)
        df_team_name = pd.DataFrame(team_name_id_list)
        df_team_name = df_team_name.iloc[:,:4]
        df_team_name.columns = ['team_id','sim_chinese','trad_chinese','english']
        df_team_id = df_team_id.append(df_team_name)
        df_team_id['league_id'] = league_id
    df_team_id = df_team_id.drop_duplicates(subset=['team_id','english'])
    # trial_on_db.insert_data('win007_team_name_id',df_team_id)


# def win007__get_transaction_volume():



#     transaction_df = trial_on_db.read_data_as_dataframe('spdex_transaction_volume')
#     options = webdriver.ChromeOptions()
#     options.add_argument("headless")
#     driver = webdriver.Chrome(r'C:\Users\ChingHo\Desktop\chromedriver.exe', chrome_options=options)
#     driver.get("https://live.aicai.com/pages/bf/jczq.shtml?issue={0}{1}{2}".format(year,month,day))
#     soup = BeautifulSoup(driver.page_source, 'html.parser')
#     driver.close()
#     match_box = soup.find_all('div', class_ = 'md_data_box css_league')
#     match_volume_data = []
#     column = ['league','home_team','ft_result','away_team','date_time','total_volume','home_volume','draw_volume','away_volume','big_home_volume','big_draw_volume','big_away_volume']
#     all_box = []
#     for match in tqdm.tqdm(match_box):
#         match_info = match.find('div',class_ = "md_tit_box")
#         league_info = match_info.find('span',class_ = "c_dgreen").text
#         match_result = match_info.find_all('span',class_ = "c_yellow")[1]
#         home_team_info = match_result.find_all('span')[0].text
#         result = match_result.find_all('span')[1].text
#         try:
#             away_team_info = match_result.find_all('span')[2].text
#         except:
#             away_team_info = result
#         time = match_info.find('span',class_ = "md_ks_time").text
#         match_content = match.find('div',class_ = 'md_con_box')
#         total_volume = match_content.find_all('div',class_ = 'proba_total')[0].find('strong',class_ = 'c_orange').text
#         data_volume = match_content.find_all('div',class_ = 'proba_data')[0]
#         home_volume = data_volume.find('span',class_ = 'c_orange').text
#         draw_volume = data_volume.find('span',class_ = 'c_green').text
#         away_volume = data_volume.find('span',class_ = 'c_blue').text
#         big_volume = match.find_all('div',class_ ='proba_data')[1]
#         big_home_volume = big_volume.find('span',class_ = 'c_orange').text
#         big_draw_volume = big_volume.find('span',class_ = 'c_green').text
#         big_away_volume = big_volume.find('span',class_ = 'c_blue').text

#         box = [[league_info,home_team_info,result,away_team_info,time,total_volume,home_volume,draw_volume,away_volume,big_home_volume,big_draw_volume,big_away_volume]]
#         all_box.extend(box)
#     df = pd.DataFrame(all_box,columns = column)
#     transaction_df = transaction_df.append(df)
#     # need create transaction_volume_table in database
#     trial_on_db.insert_data('spdex_transaction_volume',transaction_df)

