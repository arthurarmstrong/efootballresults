from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re,os
from bs4 import BeautifulSoup as BS
import pandas as pd
import sqlite3
import numpy as np
import sys,time
from datetime import datetime
from consolidate_data import consolidate_data
sys.setrecursionlimit(200000)

def main():

    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    #for tourn_id in reversed(range(323)):
    browser.get('https://kr.betsapi.com/le/23114/Esoccer-GT-Leagues--12-mins-play')
    
    page = BS(browser.page_source,'html.parser')
       
    comp = 'GT Leagues'  
    
    existing_games = opendf(f'GT Leagues/GT')
    
    season = '2020'  
    
    existing_games = get_data_from_table(page,existing_games,season)
    
    while page.find_all('li',{'class':'page-next'}):
        nexturl = 'https://kr.betsapi.com'+page.find('li',{'class':'page-next'}).find('a').get('href')
        browser.get(nexturl)
        page = BS(browser.page_source,'html.parser')
        existing_games = get_data_from_table(page,existing_games,season)
        
        if check_for_dupes(existing_games):
            print('dupes found')
            break
        
    existing_games.drop_duplicates(subset=['GAME ID'],inplace=True,keep='last')
    existing_games = consolidate_data(existing_games)
    
    existing_games.to_pickle('GT')
    conn = connect_to_database('GT.db')
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

def get_data_from_table(page,all_games,seasonyear):

    stage = 'Group Stage'
    
    #Proceed downloading game info. H3 tags are selected to get the stage of the season                                            
    for rows in page.find_all('tr'):
        cols = rows.find_all('td')
        try:
            gamedate = rows.find('td',{'class':'dt_n'}).get('data-dt')
            gamedate = time.mktime(datetime.timetuple(datetime.strptime(gamedate,'%Y-%m-%dT%H:%M:%SZ')))
        except (AttributeError, IndexError):
            #This continue statement is there to ignore any result where a date can't be parsed.
            continue

        gamedate = np.int64(gamedate)
        datestr = datetime.fromtimestamp(gamedate).strftime('%Y-%m-%d %H:%M')
        
        #Split the score into two elements, unless the score doesn't exist
        try:
            hscore, ascore = re.findall('[0-9]+',cols[3].text)
            hscore = np.float(hscore)
            ascore = np.float(ascore)
        except (AttributeError,ValueError):
            hscore = np.nan
            ascore = np.nan
            
        try:
            teams = [x.strip() for x in cols[2].text.split(' v ')]
            hometeam = re.findall('\(.*\)',teams[0])[0].strip('()')
            awayteam = re.findall('\(.*\)',teams[1])[0].strip('()')
        except IndexError:
            continue
        
        venue = np.nan
            
        gameID = str(gamedate)+hometeam+awayteam

        #Extract team name and score data, store it in a Pandas Dataframe
        gamedic= {
        'DATE':[datestr],
        'TIMESTAMP':[gamedate],
        'HOME':[hometeam],
        'AWAY':[awayteam],
        'VENUE':[venue],
        'HOME SCORE':[hscore],
        'AWAY SCORE':[ascore],
        'TOTAL':[hscore+ascore],
        'SEASON':[str(seasonyear)],#[re.search('[0-9]{8}',eachyear).group(0)],
        'GAME ID':[gameID],
        #'ROUND': [round_num+1],
        #'TEAM ID':[rows.get_attribute('data-team_id')],
        'STAGE':[stage],
        'SEASON ID':[seasonyear]
                   }
                                                             
        #This turns the new game data into a pandas dataframe
        new_game = pd.DataFrame(gamedic)
        
        #This adds the new dataframe to the complete list of games
        all_games = pd.concat([all_games,new_game],ignore_index=True,sort=False)
    return all_games

def check_for_dupes(df,subset=['GAME ID','TOTAL']):
    #This function returns TRUE if the length of the original dataframe is not the same as the 
    #length of the same dataframe with dupes from subset column removed.
    
    #If the data frame is empty there are no dupes so just return false
    if df.empty: return False
    
    #Drop unplayed games as they should be allowed to be duped
    _, df = separate(df)
    
    if len(df) == 0: return False #If there is nothing in the dataframe yet there can't be any dupes - return false
    
    if all(x in list(df.keys()) for x in subset): #proceed if all the keys passed are in the dataframe
        dupes_exist = len(df.drop_duplicates(subset=subset,inplace=False,keep='last')) != len(df)
        if dupes_exist == True: print('Found duplicates')
    else:
        dupes_exist = False
    return dupes_exist

def separate(all_games):
    #Separate played and unplayed unplayed games
    try:
        compile_list = all_games[(all_games['DATE'].values>=time.time())==True]
        compile_list.reset_index(inplace=True,drop=True)
    except TypeError:
        compile_list = pd.DataFrame([])
    try:
        result_list = all_games[all_games['DATE'].values<=time.time()]
        result_list.dropna(subset=['TOTAL','HOME SCORE','AWAY SCORE'],inplace=True)
        result_list.reset_index(inplace=True,drop=True)
    except TypeError:
        result_list = pd.DataFrame([])
    
    return compile_list, result_list
    
if __name__ == '__main__':
    main()
