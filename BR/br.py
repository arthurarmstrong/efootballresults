from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re,os
from bs4 import BeautifulSoup as BS
import pandas as pd
import sqlite3, dateparser
import numpy as np
import time
from datetime import datetime
from consolidate_data import consolidate_data

def main(browser=None):
    
    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    browser.get('https://in.betradar.com/betradar/index.php')
    input('Please sign in and go to the results tab and hit enter to continue.')
    #browser.add_cookie
    
    try:
        browser.switch_to_frame('innerframe')
    except:
        pass
    
    try:
        browser.find_element_by_link_text('Advanced version').click()
        time.sleep(1)
    except:
        pass
    
    sport = 'Aussie rules'
    catsel = 'Australia'
    event = 'All tournaments'
    
    
    sportsel_select = browser.find_element_by_id('sportsel_adv')
    catsel_select = browser.find_element_by_id('catsel_adv')
    days_select = browser.find_element_by_id('days')
    event_select = browser.find_element_by_id('toursel_adv')
    
    #Click the entire last week button
    [x for x in days_select.find_elements_by_tag_name('option')][-1].click()
    #Click into sport
    [x for x in sportsel_select.find_elements_by_tag_name('option') if x.get_attribute('text') == sport][0].click()
    time.sleep(2)
    #click into Electronic League
    [x for x in catsel_select.find_elements_by_tag_name('option') if x.get_attribute('text') == catsel][0].click()
    time.sleep(2)
    #click into requested event
    [x for x in event_select.find_elements_by_tag_name('option') if x.get_attribute('text') == event][0].click()
    time.sleep(2)
    
    existing_games = opendf(f'{catsel}{event}')
    
    ref_timestamp = time.time()
    weeks = 104
    
    for wk in range(weeks):
        #Set date range  
        today_time_struct = time.gmtime(ref_timestamp)
        from_date_struct = time.gmtime(ref_timestamp - 6*24*3600)
        
        from_date_elem = browser.find_element_by_id('fromDate')
        to_date_elem = browser.find_element_by_id('toDate')
        from_date = time.strftime("%Y-%m-%d",from_date_struct)
        to_date = time.strftime("%Y-%m-%d",today_time_struct)
        browser.execute_script('document.getElementById("fromDate").value = "'+from_date+'"')
        browser.execute_script('document.getElementById("toDate").value = "'+to_date+'"')
        
        #click search button
        browser.find_element_by_name('go').click()
        time.sleep(2)
        
        page = BS(browser.page_source,'html.parser')
        existing_games = get_data_from_table(existing_games,page)
                
        ref_timestamp -= 7*24*3600
        
    existing_games = fix_names(existing_games)
    existing_games = consolidate_data(existing_games)
    
    existing_games.drop_duplicates(subset=['GAME ID'],inplace=True,keep='last')
    
    
    conn = connect_to_database(f'{catsel}{event}.db')
    existing_games.to_pickle(f'{catsel}{event}')
    existing_games.to_sql('MATCHES',conn,index=False)
    conn.commit()
    conn.close()
    #browser.close()
    
def get_data_from_table(existing_games,page):
    
    tables = page.find_all('table',{'class':'searchResultTable'})
    if not tables: return existing_games

    for table in tables:
        
        datestr = table.find('tbody').find('td').text.strip()
        
        
        for row in table.find_all('tr')[1:]:
                        
            cols = row.find_all('td')
            
            try:
                if 'font-weight:bold' in cols[0].get('style'):
                    compname = cols[0].text.replace(u'\xa0', ' ').replace('  ',' ').strip(' -')
                    continue
            except:
                pass

            try:
                gmtime = cols[1].text
            except:
                continue
            
            gametimestr = datestr+' '+gmtime
            utctime_struct = datetime.utctimetuple(dateparser.parse(gametimestr))
            time_stamp = time.mktime(utctime_struct)
            

            hometeam,awayteam,fix_names = get_names(cols[0].text)
            homescore,awayscore = [int(x) for x in cols[2].text.split(':')]
            gameid = str(time_stamp)+hometeam+awayteam


            gamedic= {
            'DATE':[datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d %H:%M')],
            'TIMESTAMP':[time_stamp],
            'COMPETITION':[compname],
            'HOME':[hometeam],
            'AWAY':[awayteam],
            'VENUE':[np.nan],
            'HOME SCORE':[homescore],
            'AWAY SCORE':[awayscore],
            'TOTAL':[homescore+awayscore],
            'SEASON':[utctime_struct[0]],
            'GAME ID':[gameid],
            'FIX NAMES':[fix_names],
            'RAW NAMES STRING':[cols[0].text],
            'STAGE':['Group Stage'],
                       }
                                                                 
            #This turns the new game data into a pandas dataframe
            new_game = pd.DataFrame(gamedic)
            #This adds the new dataframe to the complete list of games
            existing_games = pd.concat([existing_games,new_game],ignore_index=True,sort=False)
    return existing_games 

def opendf(df):
    if df in os.listdir():
        return pd.read_pickle(df)
    else:
        return pd.DataFrame([])
    
def get_names(s):
    #Team names may not be able to be parsed. In that case save a note in boolean form that will indicate it needs postprocessing
    try:
        hometeam,awayteam = [x.strip() for x in s.split(' - ')]
        return hometeam,awayteam,False
    except:
        return 'Unknown','Unknown',True

def fix_names(df):
    unique_names = set(df['HOME'].values).union(set(df['AWAY'].values))
    
    for i in df.index.values:
        thisgame = df.loc[i]
        
        if thisgame['FIX NAMES']:
            name_matches = []
            for n in unique_names:
                if n in thisgame['RAW NAMES STRING']:
                    name_matches.append(n)
        
            if len(name_matches) == 2:
                m1_pos = thisgame['RAW NAMES STRING'].find(name_matches[0])
                m2_pos = thisgame['RAW NAMES STRING'].find(name_matches[1])
                if m1_pos < m2_pos:
                    df.at[i,'HOME'] = name_matches[0]
                    df.at[i,'AWAY'] = name_matches[1]
                elif m1_pos > m2_pos:
                    df.at[i,'HOME'] = name_matches[1]
                    df.at[i,'AWAY'] = name_matches[0]
                df.at[i,'GAME ID'] = str(thisgame['TIMESTAMP'])+df.at[i,'HOME']+df.at[i,'AWAY']
                df.at[i,'FIX NAMES'] = False
                
    return df    
    
def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

if __name__ == '__main__':
    main(browser)