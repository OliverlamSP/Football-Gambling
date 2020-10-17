# Extract feature from time series data odd change (3 days before the match start) 

import numpy as np
import datetime
import pandas as pd
import tqdm
from tsfresh import extract_features
from tsfresh import extract_relevant_features
import warnings
def split_home(row):
    try:
        return row['FT_Result'].split('-')[0]
    except:
        return np.nan
def split_away(row):
    try:
        return row['FT_Result'].split('-')[1]
    except:
        return np.nan
def change_score(row):
    if row['away_goal'] == 'Jan':
        return 1
    if row['away_goal'] == 'Feb':
        return 2
    if row['away_goal'] == 'Mar':
        return 3
    if row['away_goal'] == 'Apr':
        return 4
    if row['away_goal'] == 'May':
        return 5
    if row['away_goal'] == 'Jun':
        return 6
    if row['away_goal'] == 'Jul':
        return 7
    if row['away_goal'] == 'Aug':
        return 8
    if row['away_goal'] == 'Sep':
        return 9    
    if row['away_goal'] == 'Oct':
        return 10  
    if row['away_goal'] == 'Nov':
        return 11
    if row['away_goal'] == 'Dec':
        return 12
    else:
        return row['away_goal']
def check_median(df):
    if int(df['home_goal'].iloc[0]) - int(df['away_goal'].iloc[0]) > -df['median'].iloc[0]:
        return df['odd'].iloc[0],df['odd'].iloc[-1],df['median'].iloc[-1],df['median'].iloc[0],'home'

    if int(df['home_goal'].iloc[0]) - int(df['away_goal'].iloc[0]) == -df['median'].iloc[0]:
        return df['odd'].iloc[0],df['odd'].iloc[-1],df['median'].iloc[-1],df['median'].iloc[0],'draw'

    if int(df['home_goal'].iloc[0]) - int(df['away_goal'].iloc[0]) < -df['median'].iloc[0]:
        return df['odd'].iloc[0],df['odd'].iloc[-1],df['median'].iloc[-1],df['median'].iloc[0],'away'

    
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

def adjust_date_and_time_starting_time(row):
    return datetime.datetime.strptime(row,'%d/%m/%Y %H:%M')

def days_hours_minutes(td):
    return td.days * 24 * 60 + td.seconds / 60

def preprocessing_match_detail_and_time_series_data(league_id):
    df = pd.read_csv('win007_asian_odd_change_{}.csv'.format(league_id),low_memory = False)
    match_detail_df = pd.read_csv('win007_match_detail.csv',low_memory = False)
    match_detail_df['home_goal'] = match_detail_df.apply(split_home,1)
    match_detail_df['away_goal'] = match_detail_df.apply(split_away,1)
    match_detail_df['away_goal'] = match_detail_df.apply(change_score,1)
    df = df[df['status'] != '滚' ]
    df = df[df['company_id'] == 12]
    match_detail_df = match_detail_df[~match_detail_df['home_goal'].isnull()]
    match_detail_df['starting_time'] = match_detail_df['Date_Time']
    match_detail_df['match_id'] = match_detail_df['Match_id']
    match_detail_df = match_detail_df[['match_id','home_goal','away_goal','starting_time']]
    df['median'] = df['median'].apply(change_chinese_bet_result_to_number)
    df['odd'] = df['odd'].astype(float)
    df = df[df['bet_option'] == 'Home']
    all_match_result_df= pd.DataFrame()
    all_time_series_data_df = pd.DataFrame()
    time_stamp_list = []
    for k in range(10,1333):
        time_stamp_list.append(k*3)
    for match_id in tqdm.tqdm(df['match_id'].unique()):
        try:
            df1 = df[df['match_id'] ==match_id]
            match_detail_df_1 = match_detail_df[match_detail_df['match_id']==match_id]
            new_df = pd.merge(df1,match_detail_df_1,on = 'match_id')
            new_df['starting_time'] = new_df['starting_time'].apply(adjust_date_and_time_starting_time,1)
            new_df['date_time'] = new_df.apply(adjust_date_and_time, 1)
            new_df['before_kick_off'] = new_df['starting_time'] - new_df['date_time']
            new_df['before_kick_off'] = new_df['before_kick_off'].apply(days_hours_minutes)
            new_df['before_kick_off'] = new_df['before_kick_off'].astype(int) 
            new_df = new_df.sort_values(by = ['before_kick_off'])
            new_df = new_df[new_df['before_kick_off'] <= 4000]
            row_df = pd.DataFrame()
            row_df['before_kick_off'] = np.arange(4001)
            all_df = pd.merge(row_df,new_df,how = 'left',on = ['before_kick_off'])
            all_df = all_df.sort_values(by = ['before_kick_off'])
            all_df = all_df.fillna(method = 'bfill')
            all_df = all_df.fillna(method = 'ffill')
            all_df = all_df.drop_duplicates(subset = ['before_kick_off'],keep = 'first')
            all_df = all_df[all_df['before_kick_off'].isin(time_stamp_list)]
            final_odd,initial_odd,initial_median,final_median,result = check_median(all_df)
            match_result_df = pd.DataFrame([[match_id,final_odd,initial_odd,initial_median,final_median,result]],columns = ['match_id','final_odd','initial_odd','initial_median','final_median','result'])
            all_match_result_df = all_match_result_df.append(match_result_df)
            all_time_series_data_df = all_time_series_data_df.append(all_df)
        except:
            continue
    all_match_result_df.to_csv('match_result_{}.csv'.format(league_id),index=False)
    # all_time_series_data_df.to_csv('time_series_data_{}.csv'.format(league_id),index = False)


