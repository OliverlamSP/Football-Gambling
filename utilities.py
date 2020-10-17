import re
import pandas as pd
from bs4 import BeautifulSoup

def pattern_findall(pattern_string, full_string):
    pattern = re.compile(pattern_string)
    return pattern.findall(full_string)

def bs4_get_soup(response_from_url):
    data = response_from_url.text
    soup = BeautifulSoup(data,'html.parser')
    return soup

def put_odd_change_data_in_df(company_id,match_id,response_from_url,soup):

    odd = soup.find('span', id='odds2')
    row = odd.find_all('tr')
    odd_change_data_list = []
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
        odd_change_data_list.extend(box)
    return odd_change_data_list

def check_none_type_response(company_id,match_id,response_from_url,df_not_exist,league_id):
        df1 = pd.DataFrame([[company_id,match_id]],columns = ['Company_id' ,'Match_id'])
        df_not_exist = df_not_exist.append(df1)
        df_not_exist.to_csv('{}_asian_handicap_odd_change_not_exist.csv'.format(league_id), index = False)


def check_empty_odd_change_list(company_id,match_id,df_not_exist,league_id):
        df1 = pd.DataFrame([[company_id,match_id]],columns = ['Company_id' ,'Match_id'])
        df_not_exist = df_not_exist.append(df1)
        df_not_exist.to_csv('{}_asian_handicap_odd_change_not_exist.csv'.format(league_id), index = False)


def readcsv(file_name,columns):
    try:
        df = pd.read_csv(file_name)
    except:
        df = pd.DataFrame(columns = columns)
    return df

def get_combination_sets(df):
    if df.empty:
        return set()
    else:
        return set(df[['Company_id' ,'Match_id']].drop_duplicates().apply(lambda x: (x['Company_id'], x['Match_id']), 1).tolist())



