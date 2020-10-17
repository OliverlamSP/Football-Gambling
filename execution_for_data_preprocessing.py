import data_pre_processing_for_tsfresh
import tqdm
# league_id_list = [2,4,5,8,9,10,11,12,15,16,17,21,23,25,26,29,31,34,35,36,37,39,140,273,284,415]

for league_id in tqdm.tqdm(league_id_list):
	print(league_id)
	data_pre_processing_for_tsfresh.preprocessing_match_detail_and_time_series_data(league_id)