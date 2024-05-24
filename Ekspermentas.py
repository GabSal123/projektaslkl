import os

import bs4
import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import re
import pandas as pd


DATA_PATH = 'C:/USERS/gabsa/Documents/KrepsinisLKL/data/'
VALIDATION_PATH = 'C:/Users/gabsa/Documents/KrepsinisLKL/Validation/'

SEZONAI = {"2022-2023" : 32000, "2023-2024": 34000}

TEAMS = ["Wolves","CBet","Žalgiris","Nevėžis","Neptūnas","Lietkabelis","Pieno žvaigždės","Basket-Delamode","Šiauliai","Juventus","Rytas","Gargždai"]
TEAMS_FOR_URL = ["wolves-twinsbet","cbet","zalgiris","nevezis-optibet","neptunas","7bet-lietkabelis","pieno-zvaigzdes","m-basket-delamode",'siauliai',"uniclub-casino-juventus","rytas"]

BASE_GAME_API_URL = "https://eapi.web.prod.cloud.atriumsports.com/v1/embed/5/fixtures/{game_id}/statistics?sub=pbp"


BASE_TEAM_URL = "https://lkl.lt/komandos/"

ALL_FILES = os.listdir(DATA_PATH)


def create_directories():
    for team in TEAMS:
       if not check_file_exists(f"{DATA_PATH}/Players/{team}"):
           os.mkdir(f"{DATA_PATH}/Players/{team}")


def get_all_games_url(season,team="-",month="-"):
    page=1
    urls = []
    while True:
        response = requests.get(f"https://lkl.lt/loadResults?page={page}&team={team}&month={month}&season={season}")
        if(response.status_code != 200):
            print("blogas requestas")
            return
        if("Kol kas dar nesužaistos nei vienos rungtynės" in response.text):
            print("pasibaige puslapiai")
            break

        soup = BeautifulSoup(response.text,'html.parser')
        urls.append([url.find('a').get('href') for url in soup.find_all('span', class_='result')])
        page += 1

    print(f"page isviso {len(urls)}")
    return [item for sublist in urls for item in sublist]


def get_game_id_url(url):
    response = requests.get(url)

    if response.status_code != 200:
        print("Blogas requestas")
        return

    soup = BeautifulSoup(response.text,'html.parser')
    id = soup.find('script',attrs={'data-fixture-id':True}).get('data-fixture-id')
    return BASE_GAME_API_URL.format(game_id = id)



def check_file_exists(input_path: str):
    return os.path.isfile(input_path)



def get_file_name_and_data(url):
    res = requests.get(url)
    if (res.status_code != 200):
        print("blogas requestas")
        return

    response = res.json()
    name = "{c1}_vs_{c2}_{date}_{id}.json"
    return name.format(c1 = response['data']['banner']['fixture']['competitors'][0]['name'], c2 = response['data']['banner']['fixture']['competitors'][1]['name'],date=response['data']['banner']['fixture']["startDateTime"][:10], id = response['data']['banner']['fixture']['id']), response



def download_all_games(season, month, path):
    if path == "":
        path = DATA_PATH
    games_url = get_all_games_url(season,month=month)
    for url in games_url:
        pbp_url = get_game_id_url(url)
        file_name,data = get_file_name_and_data(pbp_url)
        file_path = path + file_name
        if not check_file_exists(file_path):
            with open(file_path,"w") as fh:
                json.dump(data,fh)


def extract_date(file_name):
    pattern = "\d{4}-\d{2}-\d{2}"
    format = "%Y-%m-%d"

    match = re.search(pattern, file_name)
    if match:
        return datetime.strptime(match.group(),format)
    else:
        print(f"No datetime pattern found in {file_name}")
        return ""

def get_file_names(team1,team2,date_from, date_to):
    file_names = []
    format = "%Y-%m-%d"
    d_from = datetime.strptime(date_from, format)
    d_to = datetime.strptime(date_to,format)
    for file_name in os.listdir(DATA_PATH):
        date = extract_date(file_name)
        if str(date) != "":
            if team1 in file_name and (team2 in file_name or team2 == "") and date > d_from and date < d_to:
                file_names.append(file_name)
    return file_names


def get_file_name_by_id(id):

    for file_name in os.listdir(DATA_PATH):
        if id in file_name:
            return file_name

    return ""



def get_pbp(filename, path="./data/"):
    with open(f"{path}{filename}","r") as fr:
        data = json.load(fr)["data"]["pbp"]
        temp = [value['events'] for key, value in data.items()]
        new_data = [val for val in temp]
        return new_data



def playful_json(url):
    response = requests.get(url).json()
    print(response["data"]["pbp"]["events"])

def update_stats(event_name,success,event_sub_type,stats):
    if "foul" in event_name:
        if "personal" in event_sub_type:
            stats[event_name] = stats[event_name] - 1
            return
        else:
            stats[event_name] = stats[event_name] + 1
            return

    if "pt" in event_name:
        if success:
            stats[event_name] = stats[event_name] + 1
            return
        else:
            stats["missed"] = stats[event_name] + 1
            return

    if "freeThrow" in event_name:
        if success:
            stats[event_name] = stats[event_name] +1
            return
        else:
            stats["missed"] = stats[event_name] + 1
            return
    if event_name in stats:
        stats[event_name] = stats[event_name] + 1

    return

def get_player_stats_dic(player,files, path="./data/"):
    stat = {"2pt": 0,"3pt":0,"rebound": 0, "assist": 0, "steal": 0, "block": 0,
            "turnover": 0,"foul":0,"freeThrow":0, "missed": 0}
    count = 0
    for file in files:
        played = False
        data = get_pbp(file,path)
        for i in range(len(data)):
            for play in data[i]:
                if 'name' in play and play['name'].lower() in player.lower():
                    update_stats(play['eventType'], play['success'], play['eventSubType'], stat)
                    played = True
        if played:
           count = count + 1

    return stat, count

def get_player_stats(dic,count):
    if count == 0:
        return {}
    dict = {}
    dict['points'] = (dic['2pt'] * 2 + dic['3pt'] * 3 + dic['freeThrow']) / count
    dict['def'] = (dic['rebound'] + dic['block'] + dic['steal']) / count
    dict['efc'] = (dict['points'] + dic['rebound'] + dic['assist'] + dic['steal'] + dic['block'] + dic['foul'] + dic['freeThrow'] - dic['turnover'] - dic['missed']) / count
    dict['games_played'] = count
    return dict



def get_game_data(file, team, path=DATA_PATH):
    dict = {}
    date = extract_date(file)
    count = 0
    for file_name in os.listdir(DATA_PATH):
        date_to_cmp = extract_date(file_name)
        if str(date_to_cmp) != "":
            delta = date - date_to_cmp
            if delta <= timedelta(days=7) and delta >= timedelta(days=0) and team.lower() in file_name.lower():
                count = count+1
    score1 = 0
    score2 = 0
    home = 0
    with open(f"{path}{file}", "r") as fr:
        data = json.load(fr)
        home = 1 if data['data']['fixture']['competitors'][0]['isHome'] else 0
        score1 = data['data']['fixture']['competitors'][0]['score']
        score2 = data['data']['fixture']['competitors'][1]['score']
        team1 = data['data']['fixture']['competitors'][0]['name']
        team2 = data['data']['fixture']['competitors'][1]['name']
        if not team in team1:
            score1, score2 = score2, score1
            home = not home
            team1, team2 = team2, team1

    team1 = get_short_team_name(team1)
    team2 = get_short_team_name(team2)
    if team1 == "" or team2 == "":
        print("blogas komandu pavadinimas", team1, team2)

    dict['team1'] = team1
    dict['team2'] = team2
    dict['games_played'] = count
    dict['score1'] = score1
    #dict['score2'] = score2
    dict['home'] = home
    dict['date'] = date
    return dict



def build_pd_row(file,players1,players2,team, path=DATA_PATH):
    index = 0
    dict = get_game_data(file,team, path)
    index = 0
    for player in players1:
        dict[f"p1{index}"] = player[1]['points']
        dict[f"d1{index}"] = player[1]['def']
        dict[f"e1{index}"] = player[1]['efc']
        index = index + 1

    index = 0
    for player in players2:
        dict[f"p2{index}"] = player[1]['points']
        dict[f"d2{index}"] = player[1]['def']
        dict[f"e2{index}"] = player[1]['efc']
        index = index + 1

    df1 = pd.DataFrame([dict])
    return df1


def get_all_player_for_team(url,team):
    response = requests.get(url)
    if response.status_code != 200:
        print("bad response")
        return
    soup = bs4.BeautifulSoup(response.text,'html.parser')
    names = [name.text.strip() for name in soup.find_all('div', class_=f'name text-{team} custom')]
    temp_surnames = soup.find_all('div', class_='surname flex w-100')
    surnames = [div.find('span').text for div in temp_surnames]
    players=[names[i]+' '+surnames[i] for i in range(len(surnames))]
    return players


def write_all_player_data_to_file(date_from, date_to):
    index = 0
    for team2 in TEAMS_FOR_URL:
        team = TEAMS[index]
        index = index+1
        players = get_all_player_for_team(f"{BASE_TEAM_URL}{team2}",team2)
        for player in players:
            files = get_file_names(team,"",date_from,date_to)
            temp,count = get_player_stats_dic(player,files)
            stats = get_player_stats(temp,count)
            with open(f"./data/Players/{team}/{player}_{date_to}","w",encoding="utf-8") as f:
                f.write(f"{player}\n {stats}")



def get_short_team_name(file):
    name = ""
    for team in TEAMS:
        if team.lower() in file.lower():
            name = team
    return name
def get_seven_best_players_from_game(file, team,path="./data/"):
    players = []
    data = get_pbp(file,path)

    team = get_short_team_name(team)
    #get unique players
    for i in range(len(data)):
        for play in data[i]:
            if 'name' in play and play['name'] not in players:
                players.append(play['name'])

    #get best players of this game
    player_stats_of_game = {}
    for player in players:
        temp, count = get_player_stats_dic(player,[file],path)
        player_stats_of_game[player] = get_player_stats(temp,count)

    best_players_of_game = sorted(player_stats_of_game.items(), key=lambda item:item[1]['points'] + item[1]['def'] + item[1]['efc'])[-7:]


    #get best player stats up till this game
    best_players_stats = {}

    date = str(extract_date(file))[:10]
    files = get_file_names(team,"",date_from="2000-01-01",date_to=(date))
    for player in best_players_of_game:
        temp, count = get_player_stats_dic(player[0],files)
        best_players_stats[player[0]] = get_player_stats(temp,count)
        #no stats
        if not best_players_stats[player[0]]:
           best_players_stats[player[0]] = {'points': 7, 'def': 5, 'efc': 7}

    return sorted(best_players_stats.items(), key=lambda item:item[1]['points'] + item[1]['def'] + item[1]['efc'])


def get_teams_from_file(file):
    pattern = r"(.*?)_vs_(.*?)_"
    match = re.search(pattern, file)
    return match.group(1), match.group(2)


def filter_files():
    all_files = [file for file in os.listdir(DATA_PATH) if os.path.isfile(f"{DATA_PATH}{file}")]
    files = []
    for file in all_files:
        date = extract_date(file)
        if datetime.strptime("2000-09-15","%Y-%m-%d") < date:
            files.append(file)
    return files

def build_pd_df():
    files = filter_files()
    df = pd.DataFrame()
    for file in files:
        team1, team2 = get_teams_from_file(file)
        players1 = get_seven_best_players_from_game(file,team1)
        players2 = get_seven_best_players_from_game(file,team2)
        row1 = build_pd_row(file,players1,players2,team1)
        row2 = build_pd_row(file,players2,players1,team2)
        df = pd.concat([df,row1,row2], ignore_index=True)

    #df.to_csv("C:/Users/gabsa/Documents/KrepsinisLKL/data_csv/data.csv")
    df = df.sort_values(['date'])
    df.to_csv("C:/Users/gabsa/Documents/KrepsinisLKL/data_csv/all_season_data.csv")
    return df


def find_newest_game(team1):
    date = datetime(2001,1,1)
    file_to_find = ""
    for file in os.listdir(DATA_PATH):
        if team1.lower() in file.lower():
            date_to_cmp = extract_date(file)
            if date < date_to_cmp:
                date = date_to_cmp
                file_to_find = file
    return file_to_find


def build_df_validation():
    files = os.listdir(VALIDATION_PATH)
    df = pd.DataFrame()
    for file in files:
        team1, team2 = get_teams_from_file(file)
        players1 = get_seven_best_players_from_game(file,team1,"./Validation/")
        players2 = get_seven_best_players_from_game(file,team2,"./Validation/")
        row1 = build_pd_row(file,players1,players2,team1, VALIDATION_PATH)
        row2 = build_pd_row(file,players2,players1,team2, VALIDATION_PATH)
        df = pd.concat([df,row1,row2], ignore_index=True)

    df.to_csv("./data_csv/validation.csv")
    return df

