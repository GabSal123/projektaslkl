import Tools as T
import datetime
import pandas as pd
from sklearn.preprocessing import OneHotEncoder
from sklearn import ensemble
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import GridSearchCV
import Ekspermentas as E
from sklearn.preprocessing import StandardScaler
from joblib import load,dump


season = T.SEZONAI['2023-2024']
# T.download_all_games(season)


# season = T.SEZONAI['2022-2023']
#T.download_all_games(season,"-","")


#T.create_directories()

#date_to_train = "2024-05-10"

#T.download_all_games(season,"05",f"C:/Users/gabsa/Documents/KrepsinisLKL/Validation/")

#T.write_all_player_data_to_file("2021-01-01","2023-09-15")

#T.update_games_with_players()


#best = T.get_five_best_players_from_game("Žalgiris_vs_Uniclub Casino-Juventus_2024-02-05_b3424525-32b7-11ee-b9a0-89f95e9ab706.json","Žalgiris")

#latest_zalgiris_game = T.find_newest_game("Žalgiris")


full_df = pd.read_csv("./data_csv/all_season_data.csv")
full_df = full_df.dropna(subset=['team1','team2'])

train_df = full_df[:600]
test_df = full_df[600:]


df = pd.read_csv("./data_csv/data.csv")
val = pd.read_csv("./data_csv/validation.csv")

scaler = StandardScaler()

unique_teams = pd.concat([train_df['team1'],train_df['team2']]).unique().reshape(-1,1)


encoder = OneHotEncoder(categories=[T.TEAMS, T.TEAMS], sparse_output=False)
dummy_df = pd.DataFrame({'team1': T.TEAMS, 'team2': T.TEAMS})
encoder.fit(dummy_df)

def encode_teams(df, encoder):
    encoded = encoder.transform(df[['team1', 'team2']])

    # Convert to DataFrame
    column_names = encoder.get_feature_names_out(['team1', 'team2'])
    encoded_df = pd.DataFrame(encoded, columns=column_names)

    return encoded_df


team_encoded_df = encode_teams(df,encoder)

val_encoded_df = encode_teams(val,encoder)

train_team_df = encode_teams(train_df,encoder)

test_team_df = encode_teams(test_df,encoder)



df = pd.concat([df,team_encoded_df], axis=1)

val = pd.concat([val,val_encoded_df], axis=1)

train_df.reset_index(drop=True, inplace=True)
train_df = pd.concat([train_df,train_team_df],axis=1)

test_df.reset_index(drop=True, inplace=True)
test_df = pd.concat([test_df,test_team_df], axis=1)



df = df.drop(['team1','team2',df.columns[0]], axis=1)
val = val.drop(['team1','team2',val.columns[0]], axis=1)
train_df = train_df.drop(['team1','team2','date',train_df.columns[0]], axis=1)
test_df = test_df.drop(['team1','team2','date',test_df.columns[0]], axis=1)







scores = df.pop('score1')

val_scores = val.pop('score1')

train_scores = train_df.pop('score1')

test_scores = test_df.pop('score1')

df = df.fillna(0)
val = val.fillna(0)
train_df = train_df.fillna(0)
test_df = test_df.fillna(0)

scaled = train_df.copy()

scaled[['p10', 'd10', 'e10', 'p11', 'd11', 'e11', 'p12',
       'd12', 'e12', 'p13', 'd13', 'e13', 'p14', 'd14', 'e14', 'p15', 'd15',
       'e15', 'p16', 'd16', 'e16', 'p20', 'd20', 'e20', 'p21', 'd21', 'e21',
       'p22', 'd22', 'e22', 'p23', 'd23', 'e23', 'p24', 'd24', 'e24', 'p25',
       'd25', 'e25', 'p26', 'd26', 'e26']] = scaler.fit_transform(scaled[['p10', 'd10', 'e10', 'p11', 'd11', 'e11', 'p12',
       'd12', 'e12', 'p13', 'd13', 'e13', 'p14', 'd14', 'e14', 'p15', 'd15',
       'e15', 'p16', 'd16', 'e16', 'p20', 'd20', 'e20', 'p21', 'd21', 'e21',
       'p22', 'd22', 'e22', 'p23', 'd23', 'e23', 'p24', 'd24', 'e24', 'p25',
       'd25', 'e25', 'p26', 'd26', 'e26']])


scaled_l = df.copy()

scaled_l[['p10', 'd10', 'e10', 'p11', 'd11', 'e11', 'p12',
       'd12', 'e12', 'p13', 'd13', 'e13', 'p14', 'd14', 'e14', 'p15', 'd15',
       'e15', 'p16', 'd16', 'e16', 'p20', 'd20', 'e20', 'p21', 'd21', 'e21',
       'p22', 'd22', 'e22', 'p23', 'd23', 'e23', 'p24', 'd24', 'e24', 'p25',
       'd25', 'e25', 'p26', 'd26', 'e26']] = scaler.fit_transform(scaled_l[['p10', 'd10', 'e10', 'p11', 'd11', 'e11', 'p12',
       'd12', 'e12', 'p13', 'd13', 'e13', 'p14', 'd14', 'e14', 'p15', 'd15',
       'e15', 'p16', 'd16', 'e16', 'p20', 'd20', 'e20', 'p21', 'd21', 'e21',
       'p22', 'd22', 'e22', 'p23', 'd23', 'e23', 'p24', 'd24', 'e24', 'p25',
       'd25', 'e25', 'p26', 'd26', 'e26']])


params2 = {
    "n_estimators": 500,
    "max_depth": 4,
    "min_samples_split": 5,
    "learning_rate": 0.01,
    "loss": "squared_error",
}

params = {
    "n_estimators": 100,
    "max_depth": 3,
    "min_samples_split": 5,
    "learning_rate": 0.05,
    "loss": "squared_error",
}

reg_l = ensemble.GradientBoostingRegressor(**params2)
reg_b = ensemble.GradientBoostingRegressor(**params2)

reg_b_s = ensemble.GradientBoostingRegressor(**params2)

reg_l_s = ensemble.GradientBoostingRegressor(**params2)

reg_l.fit(df,scores)
reg_b.fit(train_df,train_scores)

reg_b_s.fit(scaled,train_scores)

reg_l_s.fit(scaled_l, scores)




rf_l = ensemble.RandomForestRegressor(n_jobs=-1)
rf_b = ensemble.RandomForestRegressor(n_jobs=-1)

rf_b_s = ensemble.RandomForestRegressor(n_jobs=-1)

rf_l_s = ensemble.RandomForestRegressor(n_jobs=-1)

rf_b.fit(train_df,train_scores)
rf_l.fit(df,scores)

rf_b_s.fit(scaled,train_scores)

rf_l_s.fit(scaled_l,scores)


preds_reg_l = reg_l.predict(val)
preds_reg_b = reg_b.predict(val)
preds_rf_l = rf_l.predict(val)
preds_rf_b = rf_b.predict(val)

preds_reg_b_s = reg_b_s.predict(val)
preds_rf_b_s = rf_b_s.predict(val)
preds_big_rf = rf_b_s.predict(test_df)


preds_rf_l_s = rf_l_s.predict(val)
preds_reg_l_s = reg_l_s.predict(val)

mse_big_rf_s = mean_squared_error(test_scores,preds_big_rf)

mse_reg_l = mean_squared_error(val_scores, preds_reg_l)
mse_reg_b = mean_squared_error(val_scores,preds_reg_b)

mse_rf_l = mean_squared_error(val_scores,preds_rf_l)
mse_rf_b = mean_squared_error(val_scores,preds_rf_b)

mse_reg_b_s = mean_squared_error(val_scores,preds_reg_b_s)
mse_rf_b_s = mean_squared_error(val_scores,preds_rf_b_s)


mse_reg_l_s = mean_squared_error(val_scores,preds_reg_l_s)

mse_rf_l_s = mean_squared_error(val_scores,preds_rf_l_s)

print("reg sio sezono", mse_reg_l)
print("reg abieju sezonu", mse_reg_b)

print("rf sio sezono", mse_rf_l)
print("rf abieju sezonu", mse_rf_b)

print("reg abieju sezonu scaled", mse_reg_b_s)
print("rf abieju sezonu scaled", mse_rf_b_s)


print("rf abieju sezonu scaled (testuojama ant daug duomenu)", mse_big_rf_s)

print(" rf sio sezono scaled", mse_rf_l_s)
print("reg sio sezono scaled", mse_reg_l_s)

print("reg sio sezono preds", preds_reg_l)
print("reg abieju sezonu preds", preds_reg_b)
print("rf sio sezono preds", preds_rf_l)
print("rf abieju sezonu preds", preds_rf_b)
print("reg abieju sezonu scaled preds", preds_reg_b_s)
print("rf abieju sezonu scaled preds", preds_rf_b_s)




print("reg sio sezono scaled preds", preds_reg_l_s)
print("rf sio sezono scaled preds", preds_rf_l_s)

print("tikri\n",val_scores )

#dump(reg_l_s, "./reg_scaled.aaa")




