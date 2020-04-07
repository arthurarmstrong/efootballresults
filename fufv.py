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


if not 'browser' in locals(): 
    browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')

df = pd.DataFrame()

for tourn_id in reversed(range(323)):
    browser.get(f'https://iesa-global.com/pro/torneos.php?torneo_id={tourn_id}&sec=calendario')
    
    page=BS(browser.page_source,'html.parser')
    while True:
        page=BS(browser.page_source,'html.parser')
        if page.find('table',{'class':'table--lg'}):
            if page.find('table',{'class':'table--lg'}).text: break
        
        
    
    comp = page.find('small').text    
    stage = 'Group Stage'
    
    for row in page.find_all('tr'):
               
        try:
            datestr = row.find('td',{'class':'team-result__pass'}).text
            datetimetuple = dateparser.parse(datestr).utctimetuple()
            time_stamp = np.int64(time.mktime(datetimetuple))
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
        except:
            homescore = awayscore = np.nan
        
                    #Extract team name and score data, store it in a Pandas Dataframe
        gamedic= {
        'DATE':[time_stamp],
        'COMPETITION':[comp],
        'HOME':[hometeam],
        'AWAY':[awayteam],
        'VENUE':[np.nan],
        'HOME SCORE':[homescore],
        'AWAY SCORE':[awayscore],
        'TOTAL':[homescore+awayscore],
        'SEASON':[str(tourn_id)],#[re.search('[0-9]{8}',eachyear).group(0)],
        'GAME ID':[gameid],
        'STAGE':[stage],
        'SEASON ID':[tourn_id],
        'TOURNAMENT ID':[tourn_id]
                   }
                                                             
        #This turns the new game data into a pandas dataframe
        new_game = pd.DataFrame(gamedic)
        print(new_game.values)
        #This adds the new dataframe to the complete list of games
        df = pd.concat([df,new_game],ignore_index=True,sort=False)