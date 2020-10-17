# -*- coding: UTF-8 -*-
import pandas as pd 
import datetime
import requests
import re
from bs4 import BeautifulSoup
import web_scrapping
import os
import numpy as np 
from tsfresh import extract_features
from sklearn.externals import joblib
import re
import time
import tqdm	
def change_chinese_bet_result_to_number(row):
    median_list = {'平手':0,
                   '平手/半球':-0.25,
                   '半球':-0.5,
                   '半球/一球':-0.75,
                   '一球':-1,
                   '一球/球半':-1.25,
                   '球半':-1.5,
                   '球半/两球':-1.75,
                   '两球':-2,
                   '两球/两球半':-2.25,
                   '两球半':-2.5,
                   '两球半/三球':-2.75,
                   '三球':-3,
                   '受让半球':0.5,
                   '受让半球/一球':0.75,
                   '受让平手/半球':0.25,
                   '受让球半':1.5,
                   '受让一球/球半':1.25,
                   '受让一球':1,
                   '受让球半/两球':1.75, '受让两球':2,
                    '受让两球/两球半':2.25, '受让两球半/三球':2.75, '受让两球半':2.5}
    return median_list.get(row)

def adjust_date_and_time_starting_time(row):

    try:
        return datetime.datetime.strptime(row,'%d/%m/%Y %H:%M\r\n')
    except:
        return datetime.datetime.strptime(row,'%Y-%m-%d %H:%M')

def adjust_date_and_time(row):
    date, time = row['date_time'].split()
    month, day = date.split('-')
    hour, minute = time.split(':')
    year_string = row['starting_time']
    if int(month) == 12 and int(year_string.month) == 1:
        year = int(year_string.year) - 1
    else:
        year = year_string.year
    return datetime.datetime(int(year), int(month), int(day), int(hour), int(minute))

def days_hours_minutes(td):
    return td.days * 24 * 60 + td.seconds / 60

def check_median(df):
    return df['odd'].iloc[0],df['odd'].iloc[-1],df['median'].iloc[-1],df['median'].iloc[0]


def get_asian_odd_change(match_id,starting_time):
    time_stamp_list = []
    for k in range(10,1333):
        time_stamp_list.append(k*3)
    # starting time format: '%d/%m/%Y %H:%M'

    columns = ['company_id','match_id','bet_option','odd','median','date_time','status','starting_time']
    company_id = 12
    URL = 'http://vip.win007.com/changeDetail/handicap.aspx?id={0}&companyID={1}&I=0'.format(match_id,company_id)
    REFERER = 'http://vip.win007.com/AsianOdds_n.aspx?id={}'.format(match_id)
    header = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
    header['Referer'] = REFERER
    res = requests.get(URL,headers = header)
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

        box = [[company_id,match_id, 'Home', home_team_odds, median, date_time, status,starting_time],
            [company_id,match_id, 'Away', away_team_odds, median, date_time, status,starting_time]]
        match_odd_change_data.extend(box)
    df = pd.DataFrame(match_odd_change_data,columns = columns)
    df = df[df['status'] != '滚']
    df['starting_time'] = df['starting_time'].apply(adjust_date_and_time_starting_time,1)
    df['date_time'] = df.apply(adjust_date_and_time, 1)
    df['before_kick_off'] = df['starting_time'] - df['date_time']
    df['before_kick_off'] = df['before_kick_off'].apply(days_hours_minutes)
    df['before_kick_off'] = df['before_kick_off'].astype(int) 
    df.to_csv('trial_csv',index = False,encoding = 'UTF-8')
    df = pd.read_csv('trial_csv')
    os.remove("trial_csv")
    df = df.sort_values(by = ['before_kick_off'])
    df['median'] = df['median'].apply(change_chinese_bet_result_to_number)
    df['odd'] = df['odd'].astype(float)
    df = df[df['bet_option'] == 'Home']
    df = df[df['before_kick_off'] <= 4000]
    row_df = pd.DataFrame()
    row_df['before_kick_off'] = np.arange(4001)
    all_df = pd.merge(row_df,df,how = 'left',on = ['before_kick_off'])
    all_df = all_df.sort_values(by = ['before_kick_off'])
    all_df = all_df.fillna(method = 'bfill')
    all_df = all_df.fillna(method = 'ffill')
    all_df = all_df.drop_duplicates(subset = ['before_kick_off'],keep = 'first')
    all_df = all_df[all_df['before_kick_off'].isin(time_stamp_list)]
    final_odd,initial_odd,initial_median,final_median = check_median(all_df)
    all_df = all_df[['match_id','median','odd','before_kick_off']]
    extracted_features_df = extract_features(all_df, column_id="match_id", column_sort="before_kick_off")
    extracted_features_df = extracted_features_df.reset_index()
    info_list = [final_odd,initial_odd,initial_median,final_median]
    print(info_list)
    return extracted_features_df,info_list


def choose_model(handicap,odd_tuple,extracted_features_df):
	df = pd.DataFrame(columns = ['feature','home_chance','away_chance','prediction'])
	feature_list = [25,30,35,40,45,50,55,60,65,70,75,80,85,90,95]
	model_number_list = [1,2,3,4,5,6,7,8,9,10]
	for feature in feature_list:
		try:
			sample_df = pd.read_csv('handicap_{}_{}_{}_{}_{}_{}.csv'.format(handicap,odd_tuple[0],odd_tuple[1],odd_tuple[2],odd_tuple[3],feature))
			filename = 'handicap_{}_{}_{}_{}_{}_{}.sav'.format(handicap,odd_tuple[0],odd_tuple[1],odd_tuple[2],odd_tuple[3],feature)
			columns_list = sample_df.columns
			fianl_df = extracted_features_df[[c for c in extracted_features_df.columns if c in columns_list]]
			RFC = joblib.load(filename)
			pred = RFC.predict([fianl_df.iloc[0]])
			chance = RFC.predict_proba([fianl_df.iloc[0]])
			temp_df = pd.DataFrame([[feature,chance[0][0],chance[0][1],pred[0]]],columns = ['feature','home_chance','away_chance','prediction'])
			df = df.append(temp_df)
		except:
			continue
	return df

def get_testing_match_id(date):
	# eg 20160624 YYYYmmdd
	url = 'http://bf.win007.com/football/hg/Over_{}.htm'.format(date)
	r = requests.get(url)
	data = r.content
	soup = BeautifulSoup(data,'html.parser')
	temp_list = []
	for a in tqdm.tqdm(range(1,2000)):
		match_box = soup.find('tr', id = 'tr1_{}'.format(a))
		if match_box is None:
			break
		all_td = match_box.find_all('td')
		for x in all_td: 
			try:
				if re.match('showgoallist',x['onclick']):   
					temp_list.append(x['onclick'])		     
			except:pass
	testing_id_list = []
	match_id_time_list = []
	for match in temp_list:
		testing_id = match.split('showgoallist(')[1]
		testing_id = testing_id.split(')')[0]
		testing_id_list.append(testing_id)
	for match in testing_id_list:
		try:
			url = 'http://live.win007.com/detail/{}cn.htm'.format(match)
			referer = 'http://live.win007.com/detail/{}cn.htm'.format(match)
			header = {'User-Agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36"}
			header['Referer'] = referer
			r = requests.get(url,headers = header)
			data = r.content
			soup = BeautifulSoup(data,'html.parser')
			match_item = soup.find('div', id = 'matchItems')
			item = match_item.find_all('div',class_ = 'item')[1].text
			year = item[6:10]
			month = item[11:13]
			day = item[14:16]
			hour_minutes = item[16:25]
			match_time = day + '/' + month + '/' + year + '' + hour_minutes
			home_goal = soup.find_all('span',class_ = 'b t15')[0].text
			away_goal = soup.find_all('span',class_ = 'b t15')[1].text
			match_id_time_list.append((match,match_time,home_goal,away_goal))
			print(match,match_time,home_goal,away_goal)
		except:
			continue
	return match_id_time_list

def get_match_name(date):
	url = 'http://bf.win007.com/football/hg/Over_{}.htm'.format(date)
	r = requests.get(url)
	data = r.content
	soup = BeautifulSoup(data,'html.parser')
	temp_list = []
	name_list = []
	for a in range(1,2000):
		match_name_box = soup.find('td', id = 'ls_{}'.format(a))
		if match_name_box is None:
			break
		match_name = match_name_box.text
		name_list.append(match_name)

	for a in range(1,2000):
		match_box = soup.find('tr', id = 'tr1_{}'.format(a))
		if match_box is None:
			break
		all_td = match_box.find_all('td')
		for x in all_td: 
			try:
				if re.match('showgoallist',x['onclick']):   
					temp_list.append(x['onclick'])		     
			except:
				pass

	testing_id_list = []
	match_id_time_list = []
	for match in temp_list:
		testing_id = match.split('showgoallist(')[1]
		testing_id = testing_id.split(')')[0]
		testing_id_list.append(testing_id)
	df = pd.DataFrame()
	df['match_id'] = pd.Series(testing_id_list)
	df['match_name'] = pd.Series(name_list)
	print(len(testing_id_list),len(name_list))
	return df

def check_odd_list(handicap):
	'''(initial_odd_1,initial_odd_2,final_odd_1,final_odd_2)'''
		
	if handicap == -1.0:
	    odd_list = [(0.69,0.79,0.69,0.89),(0.69,0.79,0.89,1.19),(0.79,0.89,0.69,0.79),(0.79,0.89,0.79,0.84),
	    			(0.79,0.89,0.84,0.89),(0.79,0.89,0.94,1.04),(0.89,0.99,0.69,0.79),(0.89,0.99,0.79,0.84),
	    			(0.89,0.99,0.84,0.89),(0.89,0.99,0.89,0.92),(0.89,0.99,0.99,1.09),(0.89,0.99,1.09,1.19),
	    			(0.99,1.19,0.69,0.79),(0.99,1.19,0.79,0.84),(0.99,1.19,0.84,0.89),(0.99,1.19,0.94,0.99),
	    			(0.99,1.19,0.99,1.04),(0.99,1.19,1.09,1.19)]
		
	if handicap == -0.75:
	    odd_list = [(0.69,0.79,0.69,0.79),(0.69,0.79,0.79,0.89),(0.69,0.79,0.89,0.99),(0.69,0.79,0.99,1.19),
	    			(0.79,0.84,0.69,0.75),(0.79,0.84,0.75,0.78),(0.79,0.84,0.81,0.84),(0.79,0.84,0.84,0.89),
	    			(0.79,0.84,0.89,0.94),(0.79,0.84,0.94,0.99),(0.79,0.84,0.99,1.14),(0.84,0.89,0.69,0.79),
	    			(0.84,0.89,0.79,0.84),(0.84,0.89,0.84,0.87),(0.84,0.89,0.87,0.89),(0.84,0.89,0.94,0.99),
	    			(0.84,0.89,1.04,1.19),(0.89,0.94,0.69,0.79),(0.89,0.94,0.79,0.84),(0.89,0.94,0.84,0.89),
	    			(0.89,0.94,0.89,0.94),(0.89,0.94,0.94,1.02),(0.89,0.94,1.02,1.14),(0.94,0.99,0.79,0.89),
	    			(0.94,0.99,0.89,0.94),(0.94,0.99,0.94,0.99),(0.94,0.99,1.02,1.09),(0.94,0.99,1.09,1.19),
	    			(0.99,1.09,0.79,0.86),(0.99,1.09,0.86,0.90),(0.99,1.09,0.90,0.94),(0.99,1.09,0.94,0.97),
	    			(0.99,1.09,0.97,0.99),(0.99,1.09,0.99,1.02),(0.99,1.09,1.09,1.19),(1.09,1.19,0.69,0.89),
	    			(1.09,1.19,0.89,0.99),(1.09,1.19,0.99,1.09)]
	    
	if handicap == -0.5:
	    odd_list = [(0.69,0.74,0.69,0.79),(0.69,0.74,0.79,0.89),(0.69,0.74,0.89,0.99),(0.69,0.79,0.99,1.19),
	    			(0.74,0.79,0.77,0.79),(0.74,0.79,0.79,0.84),(0.74,0.79,0.84,0.89),(0.74,0.79,0.89,0.99),
	    			(0.79,0.84,0.75,0.78),(0.79,0.84,0.78,0.81),(0.79,0.84,0.81,0.83),(0.79,0.84,0.83,0.85),
	    			(0.79,0.84,0.86,0.88),(0.79,0.84,0.94,0.99),(0.79,0.84,0.99,1.04),(0.79,0.84,1.04,1.19),
	    			(0.84,0.89,0.72,0.77),(0.84,0.89,0.77,0.80),(0.84,0.89,0.80,0.82),(0.84,0.89,0.82,0.85),
	    			(0.84,0.89,0.85,0.87),(0.84,0.89,0.89,0.92),(0.84,0.89,0.92,0.95),(0.84,0.89,0.95,0.97),
	    			(0.84,0.89,0.99,1.02),(0.84,0.89,1.02,1.09),(0.84,0.89,1.09,1.19),(0.89,0.94,0.69,0.79),
	    			(0.89,0.94,0.79,0.82),(0.89,0.94,0.82,0.84),(0.89,0.94,0.84,0.86),(0.89,0.94,0.86,0.89),
	    			(0.89,0.94,0.90,0.92),(0.89,0.94,0.92,0.94),(0.89,0.94,0.94,0.96),(0.89,0.94,1.01,1.04),
	    			(0.89,0.94,1.04,1.09),(0.94,0.99,0.69,0.79),(0.94,0.99,0.79,0.82),(0.94,0.99,0.85,0.89),
	    			(0.94,0.99,0.92,0.95),(0.94,0.99,0.97,0.99),(0.94,0.99,0.99,1.01),(0.94,0.99,1.01,1.04),
	    			(0.94,0.99,1.04,1.07),(0.94,0.99,1.07,1.10),(0.94,0.99,1.10,1.14),(0.99,1.04,0.69,0.84),
	    			(0.99,1.04,0.84,0.89),(0.99,1.04,0.89,0.92),(0.99,1.04,0.92,0.94),(0.99,1.04,0.94,0.97),
	    			(0.99,1.01,1.00,1.01),(0.99,1.04,1.01,1.04),(0.99,1.04,1.07,1.09),(0.99,1.04,1.09,1.12),
	    			(0.99,1.04,1.12,1.19),(1.04,1.09,0.79,0.89),(1.04,1.09,0.92,0.96),(1.04,1.09,0.99,1.01),
	    			(1.04,1.09,1.01,1.04),(1.04,1.09,1.05,1.07),(1.04,1.09,1.07,1.08),(1.04,1.09,1.08,1.09),
	    			(1.04,1.09,1.10,1.11),(1.04,1.09,1.11,1.15),(1.04,1.09,1.15,1.19),(1.09,1.19,0.74,0.89),
	    			(1.09,1.19,0.89,0.94),(1.09,1.19,0.95,0.98),(1.09,1.19,0.98,1.00),(1.09,1.19,1.00,1.02),
	    			(1.09,1.19,1.02,1.04),(1.09,1.19,1.06,1.08),(1.09,1.19,1.08,1.10),(1.09,1.14,1.10,1.11),
	    			(1.09,1.14,1.12,1.13),(1.09,1.14,1.13,1.14),(1.09,1.14,1.14,1.19),(1.14,1.19,1.09,1.14),
	    			(1.14,1.19,1.15,1.16)]
	    
	if handicap == -0.25:
	    odd_list = [(0.69,0.79,0.79,0.89),(0.69,0.79,0.89,0.96),(0.69,0.79,0.96,1.04),(0.69,0.79,1.04,1.19),
	    			(0.79,0.84,0.71,0.79),(0.79,0.84,0.79,0.82),(0.79,0.84,0.83,0.86),(0.79,0.84,0.86,0.91),
	    			(0.79,0.84,0.91,0.99),(0.79,0.84,0.99,1.06),(0.84,0.89,0.79,0.84),(0.84,0.89,0.69,0.74),
	    			(0.84,0.89,0.85,0.86),(0.84,0.89,0.89,0.92),(0.84,0.89,0.92,0.95),(0.84,0.89,0.95,0.99),
	    			(0.84,0.89,0.99,1.04),(0.84,0.89,1.04,1.19),(0.89,0.94,0.69,0.79),(0.89,0.94,0.79,0.84),
	    			(0.89,0.94,0.84,0.89),(0.89,0.94,0.89,0.92),(0.89,0.94,0.94,0.96),(0.89,0.94,0.96,0.98),
	    			(0.89,0.94,0.98,1.00),(0.89,0.94,1.00,1.02),(0.80,0.94,1.02,1.05),(0.89,0.94,1.05,1.09),
	    			(0.89,0.94,1.09,1.14),(0.94,0.99,0,79,0.86),(0.94,0.99,0.86,0.89),(0.94,0.99,0.89,0.94),
	    			(0.94,0.99,0.94,0.96),(0.94,0.99,1.01,1.04),(0.94,0.99,1.05,1.07),(0.94,0.99,1.07,1.09),
	    			(0.94,0.99,1.09,1.12),(0.99,1.04,0.69,0.79),(0.99,1.04,0.82,0.89),(0.99,1.04,0.89,0.94),
	    			(0.99,1.04,0.94,0.97),(0.99,1.04,0.97,1.00),(0.99,1.04,1.00,1.02),(0.99,1.04,1.03,1.04),
	    			(0.99,1.04,1.03,1.04),(0.99,1.04,1.06,1.08),(0.99,1.04,1.08,1.10),(0.99,1.04,1.10,1.15),
	    			(1.04,1.09,0.79,0.85),(1.04,1.09,0.85,0.89),(1.04,1.09,0.89,0.94),(1.04,1.09,0.89,0.94),
	    			(1.04,1.09,0.94,0.97),(1.04,1.09,0.97,0.99),(1.04,1.09,1.01,1.04),(1.04,1.09,1.05,1.06),
	    			(1.04,1.09,1.06,1.08),(1.04,1.09,1.13,1.16),(1.04,1.09,1.16,1.19),(1.09,1.19,0.69,0.84),
	    			(1.09,1.19,0.84,0.89),(1.09,1.19,0.89,0.94),(1.09,1.19,0.94,0.99),(1.09,1.19,0.99,1.04),
	    			(1.09,1.19,1.06,1.09),(1.09,1.19,1.09,1.12),(1.09,1.19,1.15,1.17),(1.09,1.19,1.17,1.19)] 			
	    
	if handicap == 0.0:
	    odd_list = [(0.69,0.74,0.69,0.86),(0.69,0.74,0.86,1.09),(0.74,0.79,0.69,0.77),(0.74,0.79,0.77,0.85),
	    			(0.74,0.79,0.85,0.99),(0.74,0.79,0.99,1.19),(0.79,0.84,0.69,0.79),(0.79,0.84,0.81,0.87),
	    			(0.79,0.84,0.87,0.91),(0.79,0.84,0.91,0.97),(0.79,0.84,0.97,1.04),(0.79,0.84,1.04,1.19),
	    			(0.84,0.89,0.69,0.77),(0.84,0.89,0.77,0.81),(0.84,0.89,0.81,0.86),(0.84,0.89,0.88,0.92),
	    			(0.84,0.89,0.88,0.92),(0.84,0.89,0.92,0.96),(0.84,0.89,0.96,1.02),(0.84,0.89,1.10,1.19),
	    			(0.84,0.89,1.04,1.09),(0.89,0.94,0.74,0.81),(0.89,0.94,0.81,0.85),(0.89,0.94,0.85,0.89),
	    			(0.89,0.94,0.89,0.91),(0.89,0.94,0.91,0.94),(0.89,0.94,0.96,1.03),(0.89,0.94,1.03,1.09),
	    			(0.89,0.94,1.09,1.19),(0.94,0.99,0.69,0.84),(0.94,0.99,0.84,0.89),(0.94,0.99,0.89,0.94),
	    			(0.94,0.99,0.94,0.98),(0.94,0.99,0.98,1.02),(0.94,0.99,1.02,1.05),(0.94,0.99,1.08,1.14),
	    			(0.99,1.04,0.84,0.94),(0.99,1.04,0.94,0.99),(0.99,1.04,1.01,1.06),(0.99,1.04,1.06,1.19),
	    			(1.04,1.09,0.79,0.89),(1.04,1.09,0.89,0.99),(1.04,1.09,1.01,1.08),(1.04,1.09,1.10,1.19),
	    			(1.09,1.19,0.69,0.89),(1.09,1.19,0.94,1.09),(1.09,1.19,1.09,1.14)]



	if handicap == 0.25:
	    odd_list = [(0.69,0.74,0.69,0.89),(0.69,0.74,0.89,1.09),(0.74,0.79,0.89,1.09),(0.74,0.79,0.71,0.82),
	    			(0.74,0.79,0.71,0.82),(0.74,0.79,0.82,0.95),(0.74,0.79,0.95,1.19),(0.79,0.84,0.69,0.79),
	    			(0.79,0.84,0.79,0.82),(0.79,0.84,0.82,0.83),(0.79,0.84,0.83,0.86),(0.79,0.84,0.86,0.92),
	    			(0.79,0.84,0.96,1.19),(0.84,0.89,0.69,0.76),(0.84,0.89,0.76,0.81),(0.84,0.89,0.82,0.85),
	    			(0.84,0.89,0.85,0.89),(0.84,0.89,0.89,0.94),(0.84,0.89,0.94,1.02),(0.84,0.89,1.02,1.19),
	    			(0.89,0.94,0.69,0.79),(0.89,0.94,0.79,0.84),(0.89,0.94,0.84,0.89),(0.89,0.94,0.89,0.92),
	    			(0.89,0.94,0.96,0.99),(0.89,0.94,0.99,1.04),(0.89,0.94,0.99,1.04),(0.89,0.94,1.04,1.19),
	    			(0.94,0.99,0.79,0.89),(0.94,0.99,0.79,0.89),(0.94,0.99,0.89,0.95),(0.94,0.99,0.96,0.99),
	    			(0.94,0.99,0.99,1.03),(0.94,0.99,1.03,1.09),(0.94,0.99,1.09,1.25),(0.99,1.04,0.69,0.89),
	    			(0.99,1.04,0.89,0.99),(0.99,1.04,1.04,1.09),(0.99,1.04,1.09,1.19),(1.04,1.19,0.79,0.89),
	    			(1.04,1.19,0.89,0.96),(1.04,1.19,0.96,1.02),(1.04,1.19,1.02,1.07),(1.04,1.19,1.07,1.12),
	    			(1.04,1.19,1.07,1.12)]

	    
	if handicap == 0.5:
	    odd_list = [(0.69,0.74,0.74,0.99),(0.74,0.79,0.74,0.79),(0.74,0.79,0.79,0.89),(0.74,0.79,0.89,1.19),
	    			(0.79,0.84,0.69,0.79),(0.79,0.84,0.84,0.89),(0.79,0.84,0.89,1.19),(0.84,0.89,0.69,0.79),
	    			(0.84,0.89,0.79,0.84),(0.84,0.89,0.79,0.84),(0.84,0.89,0.84,0.89),(0.84,0.89,0.89,1.04),
	    			(0.89,0.94,0.69,0.84),(0.89,0.94,0.84,0.89),(0.89,0.94,0.94,0.99),(0.89,0.94,0.99,1.14),
	    			(0.94,0.99,0.79,0.89),(0.94,0.99,0.89,0.99),(0.94,0.99,0.99,1.04),(0.94,0.99,1.04,1.19),
	    			(0.99,1.04,0.79,0.99),(1.04,1.19,0.69,0.89),(1.04,1.19,0.89,0.99),(1.04,1.19,0.99,1.09),
	    			(1.04,1.19,1.09,1.14),(1.04,1.19,1.14,1.19)]   
	
	if handicap == 0.75:  
		odd_list = [(0.69,0.89,0.79,0.99),(0.89,0.99,0.79,0.94),(0.89,0.99,0.94,1.19)]
	
	return odd_list

def get_match_id_and_match_name(month,week):
	# day_list = ['01','02','03','04','05','06','07']
	# day_list = ['08','09','10','11','12','13','14']
	# day_list = ['15','16','17','18','19','20','21']
	# day_list = ['22','23','24','25','26','27','28','29','30','31']
	day_list = ['28','29','30']
	empty_df = pd.DataFrame()
	for day in day_list:
		da = '2019{0}{1}'.format(month,day)
		print(da)
		df = get_match_name(da)
		empty_df = empty_df.append(df)
		print(empty_df.shape)

	empty_df.to_csv('back_test_result_match_name_{}_{}csv.csv'.format(month,week),encoding = 'utf8',index = False)
	writer = pd.ExcelWriter('back_test_match_name_{}_{}excel.xlsx'.format(month,week), engine='xlsxwriter')
	empty_df.to_excel(writer,encoding = 'utf8',index = False)
	writer.save()
	
def backtest_result(month,week):
	# month format should be in double digits
	# day_list = ['01','02','03','04','05','06','07','08','09','10','11','12','13','14','15','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30']
	# day_list = ['01','02','03','04','05','06','07']
	# day_list = ['08','09','10','11','12','13','14']
	# day_list = ['15','16','17','18','19','20','21']
	# day_list = ['22','23','24','25','26','27','28','29','30','31']
	day_list = ['28','29','30']
	back_test_df = pd.DataFrame()
	for day in tqdm.tqdm(day_list):
		da = '2019{0}{1}'.format(month,day)
		match_id_time_list = get_testing_match_id(da)

		for match in tqdm.tqdm(range(0,len(match_id_time_list))):
			print(da)
			try:
				print(match_id_time_list[match][0])
				extracted_features_df,info_list = get_asian_odd_change(match_id_time_list[match][0],match_id_time_list[match][1])
				initial_handicap = info_list[2]
				final_handicap = float(info_list[3])
				home_goal = int(match_id_time_list[match][2])
				away_goal = int(match_id_time_list[match][3])
				
				if int(match_id_time_list[match][2]) - int(match_id_time_list[match][3]) > -float(info_list[3]):
					result = 'Home'
				elif int(match_id_time_list[match][2]) - int(match_id_time_list[match][3]) < -float(info_list[3]) :
					result = 'Away'
				else:
					result = 'Draw'

				odd_list = check_odd_list(initial_handicap)
				    
				for odd_tuple in odd_list:
				    if (float(info_list[1]) >= odd_tuple[0] ) and (float(info_list[1]) < odd_tuple[1] ) and (float(info_list[0]) >= odd_tuple[2]) and (float(info_list[0]) < odd_tuple[3]):
				    	df = choose_model(initial_handicap,odd_tuple,extracted_features_df)
				        df['match_id'] = match_id_time_list[match][0]
				        df['starting_time'] = match_id_time_list[match][1]
				        df['initial_handicap'] = initial_handicap
				        df['final_handicap'] = final_handicap
				        df['final_odd_range'] = '{0}-{1}'.format(odd_tuple[2],odd_tuple[3])
				        df['initial_odd_range'] = '{0}-{1}'.format(odd_tuple[0],odd_tuple[1])
				        df['final_odd'] = info_list[0]
				        df['result'] = result
				        df['home_goal'] = home_goal
				        df['away_goal'] = away_goal

				        back_test_df = back_test_df.append(df)
			except :
				continue
		back_test_df.to_csv('back_test_result_{}_{}.csv'.format(month,week),index = False)

def combined_backtest_and_match_name(month,week):
	df = pd.read_excel('back_test_match_name_{}_{}excel.xlsx'.format(month,week))
	all_df = pd.read_csv('back_test_result_{}_{}.csv'.format(month,week))
	all_df['match_id'] = all_df['match_id'].astype(int)
	df['match_id'] = df['match_id'].astype(int)
	print(len(all_df['match_id'].unique()),len(df['match_id'].unique()))
	df1 = pd.merge(all_df,df,on = 'match_id')
	writer = pd.ExcelWriter('back_test_result_combined_{}_{}.xlsx'.format(month,week), engine='xlsxwriter')
	df1.to_excel(writer,encoding = 'utf8',index = False)
	writer.save()

get_match_id_and_match_name('09','Sep')
backtest_result('09','Sep')
combined_backtest_and_match_name('09','Sep')


