from tsfresh import extract_features
from tsfresh import extract_relevant_features
import pandas as pd
from tsfresh import select_features
import tqdm
def check_result(row):
    if row['result'] == 'home':
        return 0
    elif row['result'] == 'away':
        return 1
    else: 
        return 'draw'

df = pd.read_csv('match_result_36.csv')
# median_list = df['initial_median'].unique()
# median_list.sort()
# median_list = [-3,-2.75,-2.5,-2.25,-2.0,-1.75,-1.5,-1.25,-1.0,-0.75]
# median_list = [3,2.75,2.5,2.25,2.0,1.75,1.5,1.25,1.0,0.75]
# median_list = [0.5]
median_list = [0.25]
# median_list = [0.0]
# median_list = [-0.25]
# median_list = [-0.5]
for median in tqdm.tqdm(median_list):
	all_extracted_features_df = pd.DataFrame()
	print(median)
	for league_id in tqdm.tqdm([2,4,5,8,9,10,11,12,15,17,21,23,25,26,29,31,34,35,36,37,39,140,273,284,415]):
		match_result_df = pd.read_csv('match_result_{}.csv'.format(league_id))
		match_result_df = match_result_df[match_result_df['initial_median'] == median]
		match_id_list = list(match_result_df['match_id'].unique())
		feature_df = pd.read_csv('time_series_data_{}.csv'.format(league_id))
		feature_df['before_kick_off'] = feature_df['before_kick_off'].astype(int)
		feature_df = feature_df[feature_df['before_kick_off'] > 29]
		feature_df['match_id'] = feature_df['match_id'].astype(int)
		feature_df = feature_df.dropna()
		# feature_df store the time series data 
		feature_df = feature_df[['match_id','median','odd','before_kick_off']]
		for match_id in tqdm.tqdm(match_id_list): 
			feature_match_id_df = feature_df[feature_df['match_id'] == match_id]
			extracted_features_df = extract_features(feature_match_id_df, column_id="match_id", column_sort="before_kick_off")
			all_extracted_features_df = all_extracted_features_df.append(extracted_features_df)
	all_extracted_features_df.to_csv('extracted_feature_median_{}.csv'.format(median))

'''selecting features'''
# extracted_features_df = pd.read_csv('extracted_feature_median_{}.csv'.format(test_median))
# match_result_df = pd.read_csv('match_result.csv')
# final_df = pd.merge(extracted_features_df,match_result_df,how='left', left_on=['id'], right_on=['match_id'])
# final_df = final_df.drop('match_id',axis = 1)
# final_df = final_df.dropna(axis = 1)

# final_df = final_df.set_index('id')
# final_df['result'] = final_df.apply(check_result,axis = 1)
# final_df = final_df[final_df['result']!= 'draw']
# y = final_df['result']
# X = final_df.drop('result',1)
# selected_features_df = select_features(X,y,fdr_level = 0.05)
# selected_features_df.to_csv('selected_features_median_{}.csv'.format(test_median))
