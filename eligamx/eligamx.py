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

def main():

    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    
    #for tourn_id in reversed(range(323)):
    browser.get(f'http://e.ligamx.net/cancha/partidos')
    
    page = BS(browser.page_source,'html.parser')
    while True:
        page=BS(browser.page_source,'html.parser')
        if page.find('ul',{'class':'selector-matches'}):
            if page.find('ul',{'class':'selector-matches'}).text: break
        
    comp = page.find('div',{'id':'subMail'}).text
    season = re.findall('[0-9]{4}\-*[0-9]*',comp)[0].strip()
    comp = comp.split(' / ')[0].strip()

    stage = 'Group Stage'
    
    existing_games = opendf(f'eligamx-{comp}')  
    
    matchdays = [x.get_attribute('data-nojnda') for x in browser.find_element_by_class_name('selector-matches').find_elements_by_tag_name('li')]
    
    for matchday in matchdays:
        
        #click the matchday button
        [x for x in browser.find_element_by_class_name('selector-matches').find_elements_by_tag_name('li') if x.get_attribute('data-nojnda') == matchday][0].click()
    
        page = BS(browser.page_source,'html.parser')
    
        for row in page.find_all('div',{'class':'cntPrtdo'}):
                   
            try:
                datestr = row.find('span',{'class':'date'}).text+'/2020 '+row.find('span',{'class':'hour'}).text
                datestr = datestr.replace('hr','').strip()
                datetimetuple = dateparser.parse(datestr,settings={'DATE_ORDER': 'DMY'}).utctimetuple()
                time_stamp = np.int64(time.mktime(datetimetuple))
                #correct for timezone
                time_stamp += 6*3600
            except:
                continue
            
            try:
                #get the href with the team names in it
                h = row.findNext('div',{'class':'sub-menu'}).findNext('ul',{'class':'nacionalMarcador'}).find('a').get('href')
                awayteam = ' '.join([x.capitalize() for x in re.findall('-vs-.*-jornada',h)[0].replace('-vs-','').replace('-jornada','').replace('-',' ').split(' ')])
                hometeam = ' '.join([x.capitalize() for x in re.findall('a-minuto-.*-vs',h)[0].replace('a-minuto-','').replace('-vs','').replace('-',' ').split(' ')])
                gameid = str(time_stamp)+hometeam+awayteam
            except:
                continue
        
            try:
                print 
                homescore,awayscore = [int(x) for x in re.findall('[0-9]+',row.find('div',{'class':'score'}).text)[:2]]
                print(homescore,awayscore)
            except:
                homescore = awayscore = np.nan
            
            venue = row.find('span',{'class':'stadium'})
            if venue:
                venue = venue.text
            else:
                venue = np.nan
            
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
            'SEASON':[season],
            'GAME ID':[gameid],
            'STAGE':[stage],
                       }
                                                                 
            #This turns the new game data into a pandas dataframe
            new_game = pd.DataFrame(gamedic)
            #This adds the new dataframe to the complete list of games
            existing_games = pd.concat([existing_games,new_game],ignore_index=True,sort=False)
        
    
    existing_games.drop_duplicates(subset=['GAME ID'],inplace=True,keep='last')
    
    conn = connect_to_database(f'eligamx-{comp}.db')
    existing_games.to_pickle(f'eligamx-{comp}')
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
