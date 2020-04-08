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

def main(tourn_id):

    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    
    #for tourn_id in reversed(range(323)):
    browser.get(f'https://iesa-global.com/pro/torneos.php?torneo_id={tourn_id}&sec=calendario')
    
    page = BS(browser.page_source,'html.parser')
    while True:
        page=BS(browser.page_source,'html.parser')
        if page.find('table',{'class':'table--lg'}):
            if page.find('table',{'class':'table--lg'}).text: break
        
    comp = page.find('small').text    
    stage = 'Group Stage'
    
    existing_games = opendf(f'FUFV/{comp}')
    existing_games = get_history_from_master(existing_games,comp)    
    
    for row in page.find_all('tr'):
               
        try:
            datestr = row.find('td',{'class':'team-result__pass'}).text
            datetimetuple = dateparser.parse(datestr).utctimetuple()
            time_stamp = np.int64(time.mktime(datetimetuple))
            #correct for timezone
            time_stamp += +4*3600
            gameid=row.find('td').text
        except:
            continue
        
        try:
            hometeam = row.find_all('td')[3].text.strip()
            awayteam = row.find_all('td')[5].text.strip()
        except:
            continue
    
        try:
            homescore,awayscore = [int(x) for x in re.findall('[0-9]+',row.find_all('td')[4].text)[:2]]
            print(homescore,awayscore)
        except:
            homescore = awayscore = np.nan
        
                    #Extract team name and score data, store it in a Pandas Dataframe
        gamedic= {
        'DATE':[datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M')],
        'TIMESTAMP':[time_stamp],
        'COMPETITION':[comp],
        'HOME':[hometeam],
        'AWAY':[awayteam],
        'VENUE':[np.nan],
        'HOME SCORE':[homescore],
        'AWAY SCORE':[awayscore],
        'TOTAL':[homescore+awayscore],
        'SEASON':[str(tourn_id)],
        'GAME ID':[gameid],
        'STAGE':[stage],
        'SEASON ID':[tourn_id],
        'TOURNAMENT ID':[tourn_id]
                   }
                                                             
        #This turns the new game data into a pandas dataframe
        new_game = pd.DataFrame(gamedic)
        #This adds the new dataframe to the complete list of games
        existing_games = pd.concat([existing_games,new_game],ignore_index=True,sort=False)
        
    
    existing_games.drop_duplicates(subset=['GAME ID'],inplace=True,keep='last')
    
    
    conn = connect_to_database(f'FUFV/{comp}.db')
    existing_games.to_pickle(f'FUFV/{comp}')
    existing_games.to_sql('MATCHES',conn,index=False)
    conn.commit()
    conn.close()
    browser.close()
    
def get_history_from_master(df,comp):
    
    master = pd.read_pickle(f'FUFV/fufv.pkl')
    
    history = master[master['COMPETITION']==comp]
    
    df = pd.concat([df,history],ignore_index=True,sort=False)
    
    return df
    
def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

def opendf(df):
    if df in os.listdir():
        return pd.read_pickle(df)
    else:
        return pd.DataFrame([])
    
if __name__ == '__main__':
    main(tourn_id=322)
    main(tourn_id=323)
