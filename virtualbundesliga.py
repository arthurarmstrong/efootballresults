from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re,os
from bs4 import BeautifulSoup as BS
import pandas as pd
import sqlite3, dateparser
import numpy as np
import pickle
import sys,time
from datetime import datetime
from consolidate_data import consolidate_data
sys.setrecursionlimit(200000)


def main(browser=None):
    
    conn = connect_to_database('virtualbundesliga.db')
    c = conn.cursor()
    df = opendf('virtualbundesliga')
    
    #get an instance of chrome going
    if not browser:
        browser =  openBrowser(headless=False)
    else:
        pass

    for i in range(1,22):
        browser.get('https://virtual.bundesliga.com/en/club-championship/spieltage/'+str(i))
        
        #Use Beautiful Soup and Pandas to bring in the info
        new_results = get_results(browser)
        df = pd.concat([new_results,df],ignore_index=True,sort=False)
        print (df)
        
    #Create date timestamps
    df = make_timestamps(df)
    
    #look for values that should be cansolidated
    df = consolidate_data(df)
    df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
    
    #Send it to the database
    df.to_sql('MATCHES',conn,if_exists='replace',index=False)
    df.to_pickle('esportsbattle')
    
    #Close up
    print ('Successfully completed.')
    conn.commit()
    conn.close()
    browser.close()
    return df

def get_results(browser):
    
    games = []
    page  = BS(browser.page_source,'html.parser')
    
    #wait for elements to load
    while not page.find('div',{'class':'m02__match'}):
        print('No matches found. Waiting for them to load..')
        time.sleep(2)
        page  = BS(browser.page_source,'html.parser')

    
    for match in page.find_all('div',{'class':'m02__match'}):
        
            gamedate = get_game_date(match)
            
            teams = get_teams(match)
            if not teams:
                print('Problem getting team names')
                continue
            hometeam,awayteam = teams
        
            homescore, awayscore = get_score(match)
            
            #Turn these returned values into a dictionary and append to the list of games
            games.append({'GAME_DATE':gamedate, 'HOME':hometeam,'AWAY':awayteam,'HOME SCORE':homescore,'AWAY SCORE':awayscore,'STAGE':'Group Stage'})

        
    df = pd.DataFrame(data=games)
    return df

def get_game_date(match):
    
    gamedate = match.find('div',{'class':'m02__match__round'}).text
    gamedate = re.findall('[0-9]{2}\.[0-9]{2}\.[0-9]{4}, [0-9]+:[0-9]+',gamedate)[0]
    
    return gamedate
    
def get_playing_as(r):
    spl = r.text.split(' - ')
    try:
        home = re.findall(' .*\(',spl[0])[0]
        home = home.strip()[:-1]
        away = spl[1][:spl[1].find('(')].strip()
    except:
        return None, None
    
    return home, away
                
def get_date(article):
        
    for a in article.find_all('a',{'href':re.compile('esportsbattle/posts/')}):
        
        a = a.text
        try:
            article_date = dateparser.parse(a)
            return article_date
        except:
            continue

        print ('No date found')
        return False
    
def get_score(match):
    
    score = match.find('div',{'class':'m01__games__game'})
    
    if not score:
        return np.nan,np.nan
    else:
        homescore, awayscore = [x for x in score.text.split(':')]
        return int(homescore),int(awayscore)

def get_teams(match):
    
    teams = match.find_all('div',{'class':'m02__match__opponent__name'})
    if len(teams) != 2:
        return False
    else:
        return [x.text for x in teams]

def openBrowser(headless=True):
    
    chrome_options = Options()
    if headless == True:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        print('Browser opening in headless mode')
    
    #Starts a new instance of Chrome using Selenium webdriver
    if not 'browser' in locals(): 
        browser = webdriver.Chrome(chrome_options=chrome_options,executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')

    return browser

def get_cookies(browser):
    
    cookies = pickle.load(open("../cookies.pkl", "rb"))
    for cookie in cookies:
        browser.add_cookie(cookie)
        
def make_timestamps(df):
    
    for i in df.index.values:
        date = df.at[i,'GAME_DATE']
        unix_time_stamp = np.int64(time.mktime(datetime.timetuple(datetime.strptime(date,'%d.%m.%Y, %H:%M'))))
        df.at[i,'DATE'] = datetime.fromtimestamp(unix_time_stamp).strftime('%Y-%m-%d %H:%M')
        df.at[i,'GAME ID'] = str(df.at[i,'DATE']) + df.at[i,'HOME']+df.at[i,'AWAY'] 
                
    return df    
    
def consolidate(df):
    
    df.sort_values(by=['ARTICLE_DATE'],axis=0,ascending=True,inplace=True)
    
    return df

def opendf(df):
    if df in os.listdir():
        return pd.read_pickle(df)
    else:
        return pd.DataFrame([])

def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

def build_table(df,season=None):

    unique_players = set()
    for team, players in teams.items():
        for player in players:
            unique_players.add(player)
    
    #Remove duplicates
    df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
    df.dropna(subset=['HOME SCORE','AWAY SCORE'],inplace=True)
    #Build zero vector to populate table with initially
    zero_column = np.zeros(len(players),dtype=int)
    #Initialise dataframe
    table = pd.DataFrame(index=teams,data={'P':zero_column,'W':zero_column,'D':zero_column,'L':zero_column,'F':zero_column,'A':zero_column,'+/-':zero_column,'Pts':zero_column,'GD Per Game':zero_column})
  
    
    for i in df.index:
        this_game = df.loc[i]
        
        h_s = int(this_game['HOME SCORE'])
        a_s = int(this_game['AWAY SCORE'])
        if h_s == a_s:
            points = [1,1]
            table.at[this_game['HOME'],'D'] += 1
            table.at[this_game['AWAY'],'D'] += 1
        if h_s > a_s:
            points = [3,0]
            table.at[this_game['HOME'],'W'] += 1
            table.at[this_game['AWAY'],'L'] += 1            
        if h_s < a_s:
            points = [0,3]
            table.at[this_game['HOME'],'L'] += 1
            table.at[this_game['AWAY'],'W'] += 1
        
        for player in unique_players():
        table.at[this_game['HOME'],'P'] += 1
        table.at[this_game['HOME'],'F'] += int(this_game['HOME SCORE'])
        table.at[this_game['HOME'],'A'] += int(this_game['AWAY SCORE'])
        table.at[this_game['HOME'],'Pts'] += points[0]
        table.at[this_game['HOME'],'+/-'] += h_s-a_s
        table.at[this_game['AWAY'],'P'] += 1
        table.at[this_game['AWAY'],'F'] += int(this_game['AWAY SCORE'])
        table.at[this_game['AWAY'],'A'] += int(this_game['HOME SCORE'])
        table.at[this_game['AWAY'],'Pts'] += points[1]
        table.at[this_game['AWAY'],'+/-'] += a_s-h_s
        
    table['GD Per Game'] = (table['F']-table['A'])/table['P']
    table = table.round(2)
    
    table.sort_values(by=['GD Per Game'],ascending=False,inplace=True)

    return table

if __name__ == '__main__':
    df  = main()
    
    teams = {'SV Werder Bremen':['Dr. Erhano','Megabit'],'SpVgg Greuther Fürth':['Fifabio97','Sweatzz_17'],'Bayer 04 Leverkusen':['deto','Dubzje'],'Borussia Mönchengladbach':['Jeffryy95','DerGaucho10'],'VfL Wolfsburg':['SaLz0r','BeneCR7x'],'VfL Bochum 1848':['Xander','Bassinho'],'Hamburger SV':['Chrissi','Leon'],'Hannover 96':['EROL','DENNINHO'],'Eintracht Frankfurt':['Andy','Danielffm1999'],'1. FC Köln':['TheStrxngeR','Phenomeno'],'VfB Stuttgart':['Burak May','Lukas_1004'],'FC Schalke 04':['Deos','Julii'],'RB Leipzig':['Cihan','osako27'],'1. FSV Mainz 05':['Bajazzo_7','Fxnzy05'],'1. FC Nürnberg':['Bubu','Serhatinho01'],'FC Augsburg':['LukasR18','xThePunisher-96'],'SV Darmstadt 98':['GOTZERY','luca_B3rna'],'FC St. Pauli':['Bero','Nico'],'Hertha BSC':['EliasN97','blackarrow'],'Arminia Bielefeld':['Krapsi','Ignite'],'Holstein Kiel':['rohwaedder','Samstag_11'],'SV Wehen Wiesbaden':['Bremo','bono']}
    