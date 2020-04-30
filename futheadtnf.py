from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re,os
from bs4 import BeautifulSoup as BS
import pandas as pd
import sqlite3, dateparser
import numpy as np
import sys,time
from datetime import datetime
from consolidate_data import consolidate_data
sys.setrecursionlimit(200000)

def main(tourn_id=None):

    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    comp = 'TNF'
    stage = 'Group Stage'
    existing_games = opendf(f'futhead_tnf/{comp}')
    
    tourn_ids = list(range(1,31))
    tourn_ids.extend([f'{x}_2' for x in range(1,32)])
    
    for tourn_id in tourn_ids:
        browser.get(f'https://challonge.com/futhead_tnf_{tourn_id}')
        
        page = BS(browser.page_source,'html.parser')
        #while True:
        #    page=BS(browser.page_source,'html.parser')
        #    if page.find('table',{'class':'table--lg'}):
        #        if page.find('table',{'class':'table--lg'}).text: break
          
        try:
            datestr = page.find('div',{'class':'start-time'}).text
        except:
            continue
        
        for row in page.find_all('g'):
                   
            try:
                datetimetuple = dateparser.parse(datestr).utctimetuple()
                time_stamp = np.int64(time.mktime(datetimetuple))
            except:
                continue
            
            try:
                hometeam,awayteam = [x.find('title').text.strip() for x in row.find_all('svg')]
                gameid = str(time_stamp)+hometeam+awayteam
            except:
                continue
        
            try:
                homescore,awayscore = [int(x.find('text',{'class':'match--player-score'}).text) for x in row.find_all('svg')]
            except:
                homescore = awayscore = np.nan
            
            print (hometeam,awayteam,homescore,awayscore,time_stamp)
            
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
    existing_games = consolidate_data(existing_games)
    
    conn = connect_to_database(f'futhead_tnf/{comp}.db')
    existing_games.to_pickle(f'futhead_tnf/{comp}')
    existing_games.to_sql('MATCHES',conn,index=False)
    conn.commit()
    conn.close()
    browser.close()

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
    main()
