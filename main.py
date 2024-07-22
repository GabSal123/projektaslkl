import numpy as np
import matplotlib.pyplot as plt
import Tools as T
import datetime
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn import ensemble
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV
import Ekspermentas as E
from sklearn.preprocessing import StandardScaler
from joblib import load,dump


season = T.SEZONAI['2023-2024']
#T.download_all_games(season)


df = pd.read_csv("./data_csv/data_new.csv")
df = df[df.columns[1:]]

df = df.sort_values('date')

df = df.dropna(subset=['team1','team2'])
df['last_game'] = df['last_game'].str.extract(r'(\d+)').astype(int)
train = df[:700].copy()
test = df[700:].copy()

train.reset_index(drop=True, inplace=True)
test.reset_index(drop=True, inplace=True)



uniq_teams = pd.concat([train['team1'],train['team2'],test['team1'],test['team2']]).unique().reshape(-1,1)

encoder = OneHotEncoder(sparse_output=False)

encoder.fit(uniq_teams)

print(encoder.categories_)


def encode_teams(dataframe,encoder):
    team1 = pd.DataFrame(data = encoder.transform(dataframe['team1'].values.reshape(-1,1)))
    team2 = pd.DataFrame(data= encoder.transform(dataframe['team2'].values.reshape(-1,1)))
    team_names = encoder.categories_
    team1_col_names = ['team1_' + name for name in team_names]
    team2_col_names = ['team2_' + name for name in team_names]
    team1.columns = team1_col_names
    team2.columns = team2_col_names
    dataframe = pd.concat([dataframe,team1,team2], axis=1)
    return dataframe

train = encode_teams(train,encoder)
test = encode_teams(test,encoder)



train_scores = train.pop('score1')
test_scores = test.pop('score1')

train = train.drop(['team1','team2','date'],axis=1)
test = test.drop(['team1','team2','date'],axis=1)

train.columns = train.columns.astype(str)
test.columns = test.columns.astype(str)

scaler = StandardScaler()

print(train.columns)

columns_to_scale = ['winrate', 'average', 'last_game', 'games_played', 'p10', 'd10',
       'e10', 'p11', 'd11', 'e11', 'p12', 'd12', 'e12', 'p13', 'd13', 'e13',
       'p14', 'd14', 'e14', 'p15', 'd15', 'e15', 'p20', 'd20', 'e20', 'p21',
       'd21', 'e21', 'p22', 'd22', 'e22', 'p23', 'd23', 'e23', 'p24', 'd24',
       'e24', 'p25', 'd25', 'e25']


scaler.fit(train[columns_to_scale])

train_scaled = train.copy()
test_scaled = test.copy()

train_scaled[columns_to_scale] = scaler.transform(train[columns_to_scale])
test_scaled[columns_to_scale] = scaler.transform(test[columns_to_scale])



params = {
    "n_estimators": 500,
    "max_depth": 4,
    "min_samples_split": 5,
    "learning_rate": 0.01,
    "loss": "squared_error",
}
reg = ensemble.GradientBoostingRegressor(**params)
reg_s = ensemble.GradientBoostingRegressor(**params)
rf = ensemble.RandomForestRegressor()
rf_s = ensemble.RandomForestRegressor()

reg.fit(train,train_scores)
rf.fit(train,train_scores)

reg_s.fit(train_scaled,train_scores)
rf_s.fit(train_scaled,train_scores)



preds_reg_s = reg_s.predict(test_scaled)
preds_rf_s = rf_s.predict(test_scaled)

preds_reg = reg.predict(test)
preds_rf = rf.predict(test)

print(f"xg mse {mean_squared_error(test_scores,preds_reg)}")
print(f"xg r2 {r2_score(test_scores,preds_reg)}")
print(f"xg scaled mse {mean_squared_error(test_scores,preds_reg_s)}")
print(f"xg scaled r2 {r2_score(test_scores,preds_reg_s)}")

print(f"rf mse {mean_squared_error(test_scores,preds_rf)}")
print(f"rf r2 {r2_score(test_scores,preds_rf)}")
print(f"rf scaled mse {mean_squared_error(test_scores,preds_rf_s)}")
print(f"rf scaled r2 {r2_score(test_scores,preds_rf_s)}")

print(rf_s.feature_importances_)










# season = T.SEZONAI['2022-2023']
#T.download_all_games(season,"-","")


#T.create_directories()

#date_to_train = "2024-05-10"

#T.download_all_games(season,"05",f"C:/Users/gabsa/Documents/KrepsinisLKL/Validation/")

#T.write_all_player_data_to_file("2021-01-01","2023-09-15")

#T.update_games_with_players()


#best = T.get_five_best_players_from_game("Žalgiris_vs_Uniclub Casino-Juventus_2024-02-05_b3424525-32b7-11ee-b9a0-89f95e9ab706.json","Žalgiris")

#latest_zalgiris_game = T.find_newest_game("Žalgiris")

#hasukas = T.calculate_score_percent_players_count(0.8)

#averages = [tup[0]/tup[1] for key,tup in hasukas.items()]

#average = sum(averages)/len(averages)
#print(average)
#5.75 = 80%
#6.9 = 90%

