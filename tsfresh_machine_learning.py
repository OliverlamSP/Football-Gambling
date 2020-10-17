#Pick best fit model for different type of match


import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import datetime
import tqdm
from sklearn.feature_selection import SelectKBest
import sklearn.feature_selection
from sklearn.model_selection import KFold
from sklearn.externals import joblib
from sklearn.model_selection import train_test_split
def adjust_date_and_time_starting_time(row):
    return datetime.datetime.strptime(row,'%Y-%m-%d %H:%M')
# read data
handicap = 0.25

initial_odd_1 = 1.04
initial_odd_2 = 1.19
final_odd_1 = 1.07
final_odd_2 = 1.12
prob = 0.7
feature_number_list = [30,40,50,70,75,85]



extracted_feature_df = pd.read_csv('extracted_feature_median_{}.csv'.format(handicap))
match_id_list = extracted_feature_df['id'].unique()
df = pd.DataFrame()
league_id_list = [2,4,5,8,9,10,11,12,15,17,21,23,25,26,29,31,34,35,37,39,140,273,284,415]
for league_id in league_id_list: 
    match_result_df = pd.read_csv('match_result_{}.csv'.format(league_id))
    df = df.append(match_result_df)
all_match_result_df = df[df['match_id'].isin(match_id_list)]
df = df[df['match_id'].isin(match_id_list)]
df = df[(df['final_odd'] >= final_odd_1) & (df['final_odd'] < final_odd_2)]
df = df[(df['initial_odd'] >= initial_odd_1) & (df['initial_odd'] < initial_odd_2)]
filter_match_id_list = df['match_id'].unique()
all_match_result_df= all_match_result_df[all_match_result_df['match_id'].isin(filter_match_id_list)]
extracted_feature_df= extracted_feature_df[extracted_feature_df['id'].isin(filter_match_id_list)]

# data preprocessi1g
all_match_result_df = all_match_result_df[['match_id','result']]
dataset = pd.merge(extracted_feature_df,all_match_result_df,left_on = 'id',right_on = 'match_id')

one_hot_encoding = pd.get_dummies(pd.Series(dataset['result']))
dataset = dataset.drop(['result','match_id'],axis = 1)
dataset = pd.merge(dataset,one_hot_encoding, left_index=True, right_index=True)

try:
	dataset = dataset[dataset['draw'] == 0]
	y_1 = dataset['away']
	X = dataset.drop(['id','away','home','draw'],axis = 1)
except:
    print('Error')
    y_1 = dataset['away']
    X = dataset.drop(['id','away','home'],axis = 1)


# Remove eliminate the misiing value, infinite value 
X = X.replace([np.inf, -np.inf], np.nan)
X = X.dropna(1)
X_1 = X

# Testing the number of features gives the best performance
for k in feature_number_list:
    model = SelectKBest(k=k)
    new_X = model.fit_transform(X_1,y_1)
    final_df = pd.DataFrame() 
    # putting back to a dataframe to keep those selected columns name 
    for row in new_X:
        row_df =  pd.DataFrame([row],columns = X_1.columns[model.get_support()])
        final_df = final_df.append(row_df)
    X_2 = final_df

    '''Getting festures columns names and save into a dataframe'''
    model_df = pd.DataFrame(columns = X_1.columns[model.get_support()])
    model_df.to_csv('handicap_{}_{}_{}_{}_{}_{}.csv'.format(handicap,initial_odd_1,initial_odd_2,final_odd_1,final_odd_2,k),index = False)
    X = X_2.values 
    y = y_1.values
    cv = KFold(n_splits=10, random_state=42, shuffle=False)
    total_sample_list = []
    count_list = []

    for train_index, test_index in cv.split(X):

        X_train, X_test, y_train, y_test = X[train_index], X[test_index],y[train_index], y[test_index]
        RFC = RandomForestClassifier(max_depth = 1000, random_state=0)
        RFC.fit(X_train, y_train)
        '''saving model'''
        filename = 'handicap_{}_{}_{}_{}_{}_{}.sav'.format(handicap,initial_odd_1,initial_odd_2,final_odd_1,final_odd_2,k)
        joblib.dump(RFC, filename)
        RFC = joblib.load(filename)


        pred = RFC.predict(X_test)
        y_pred = RFC.predict_proba(X_test)
        new_list = []
        for a in range(0,len(y_pred)):
            for b in range(0,2):
                if y_pred[a][b] > prob:
                    new_list.append(a)

        ''' new_list record the position of the prediction 
          if that prediction has a probability higher than 0.8'''
        count = 0
        for c in new_list:
                
            if pred[c] == list(y_test)[c]:
                count += 1
        # count record the number of correct prediction 

        # As each model has 10 folds, the count_list will store the number of count of each fold
        count_list.append(count)
        # total_sample_list store the total number of prediction the model made
        total_sample_list.append(len(new_list))

    print(k,sum(count_list),sum(total_sample_list),len(y))

print(handicap,initial_odd_1,initial_odd_2,final_odd_1,final_odd_2,prob)
