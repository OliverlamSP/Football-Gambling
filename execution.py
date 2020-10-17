import web_scrapping
import pandas as pd 

# for scrapping match detail for win007
league_id_list = [36,37,39,35,31,8,9,34,11,12,23,29,16,17,5,26,10,2,4,21,415,14040,14044,25,284,273,15]
empty_df = pd.read_csv('win007_match_detail.csv')
for league_id in league_id_list:
    print(league_id)
    df = web_scrapping.win007__get_match_detail(str(league_id))
    empty_df = empty_df.append(df)
    empty_df.to_csv('win007_match_detail.csv',index = False)

