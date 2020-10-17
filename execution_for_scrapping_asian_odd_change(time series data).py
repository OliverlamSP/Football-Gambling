#execution script for time series data scrapping

import pandas 
import web_scrapping
league_id_list = [36,37,39,35,31,8,9,34,11,12,23,29,16,17,5,26,10,2,4,21,415,140,140,25,284,273,15]
league_id_list = [2,4,5,8,9,10,11,12,15,16,17,21,23,25,26,29,31,34,35,36,37,39,140,273,284,415]
league_id_list = [140]

for league_id in league_id_list:
	web_scrapping.win007__asian_odd_change(league_id)
