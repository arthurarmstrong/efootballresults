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
       
    #get an instance of chrome going
    if not browser:
        browser =  openBrowser()
        browser.get('https://www.facebook.com/esportsbattle')
    else:
        pass
    
    #load saved cookies
    get_cookies(browser)
    
    #refresh the page for login
    browser.refresh()

    #click all the buttons that say 'See More'
    browser, click_completed = click_seemore_buttons(browser)
    #save the page in case we want it again later
    #pickle.dump(BS(browser.page_source,'html.parser'),open('page.pkl','wb'))
    
    if click_completed:
        
        existing_results = opendf('eSportsBattle/esportsbattle')
        
        #Use Beautiful Soup and Pandas to bring in the info
        df = get_results(browser)
        df = pd.concat([df,existing_results],ignore_index=True,sort=False)
        
        #Create date timestamps
        df = make_timestamps(df)
        
        #look for values that should be cansolidated
        df = consolidate_data(df)
        df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
        
        conn = connect_to_database('eSportsBattle/esportsbattle.db')
        #Send it to the database
        df.to_sql('MATCHES',conn,if_exists='replace',index=False)
        df.to_pickle('eSportsBattle/esportsbattle')
        
        #Close up
        print ('Successfully completed.')
        conn.commit()
        conn.close()
        browser.close()
        return df
    
    else:
        print ('Did not complete clicking buttons.')
        return None
    
def click_seemore_buttons(browser,count_limit=100):
    
    counter = 0
    
    try:
        while True:
            seemore = browser.find_elements_by_link_text('See More')
            for s in reversed(seemore):
                #This try exists as sometimes links are not clickable for whatever reason. That is fine, as they will be found
                # again in another pass
                try:
                    s.click()
                    counter += 1
                    if counter % 10 == 0: print (counter)
                    if counter >= count_limit:
                        print('Reached click count limit, returning')
                        return browser,True    
                except:
                    pass
                

        #Returns a message along with browser saying that all buttons were clicked
        print('Completed clicking all buttons')
        return browser, True
    
    except WebDriverException as err:    
        #return the browser and a message saying that it did not complete successfully
        print (err)
        return browser, False

def get_results(browser):
    
    games = []
    
    page  = BS(browser.page_source,'html.parser')
    
    #get rid of any translated elements, which seem to be housed in blockquotes
    for translation in page.find_all('blockquote'):
        translation.decompose()
    
    for article in page.find_all('div',{'role':'article'}):
        article_date = get_date(article)
        
        #article_date will return false if a date is not parsed
        if article_date:
            gamedate = get_game_date(article)
            for r in article.find_all('div',{'dir':'auto'}):
                gametime = re.findall('[0-9]+:[0-9]{2}',r.text[:5])
                if gametime:
                    
                    gametime = gametime[0]
                    
                    teams = get_teams(r)
                    if not teams:
                        print('Problem getting team names')
                        continue
                    hometeam,awayteam = teams
                    if 'such' in hometeam or 'such' in awayteam: print(r.text)
                    homeplayingas,awayplayingas = get_playing_as(r)
                    
                    #If there was an error parsing names, skip
                    if not homeplayingas or not awayplayingas: continue
                
                    homescore, awayscore = get_score(r.text)
                    
                    #Turn these returned values into a dictionary and append to the list of games
                    games.append({'ARTICLE_DATE':article_date,'GAME_DATE':gamedate, 'TIME':gametime, 'HOME':hometeam,'AWAY':awayteam,'HOME SCORE':homescore,'AWAY SCORE':awayscore,'HOME_PLAYING_AS':homeplayingas,'AWAY_PLAYING_AS':awayplayingas,'STAGE':'Group Stage'})
                    
        else:
            continue
        
    df = pd.DataFrame(data=games)
    return df

def get_game_date(article):
    
    gamedate = re.findall('[0-9]{2}\.[0-9]{2}\.[0-9]{4}',article.text)
    
    if gamedate:
        gamedate = gamedate[0]
        gamedate = '-'.join(reversed([x for x in gamedate.split('.')]))
        return gamedate
    else:
        return np.nan
    
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
    
def get_score(r):
    
    score = re.findall(' [0-9]+:[0-9]+',r)
    if score:
        score = score[0].replace(' ','')
    else:
        return np.nan,np.nan

    homescore, awayscore = [str(x) for x in score.split(':')]
    return int(homescore),int(awayscore)

def get_teams(r):
    
    teams = re.findall('(?<=\().+?(?=\))',r.text)
    
    if len(teams) < 2:
        return False
    elif 'no player' in teams[0] or 'no player' in teams[1]:
        return False
    else:
        #get rid of anything that suggests a team name was less than 3 characters
        if len(teams[0]) < 3:
            print(teams[0])
            return False
        if len(teams[1]) < 3:
            print(teams[1])
            return False
        return teams[:2]

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
        if type(df.at[i,'GAME_DATE'])==str and type(df.at[i,'TIME'])==str:
            date = ' '.join([df.at[i,'GAME_DATE'],df.at[i,'TIME']])
            unix_time_stamp = np.int64(time.mktime(datetime.timetuple(datetime.strptime(date,'%Y-%m-%d %H:%M'))))
            df.at[i,'DATE'] = datetime.fromtimestamp(unix_time_stamp).strftime('%Y-%m-%d %H:%M')
            df.at[i,'GAME ID'] = str(df.at[i,'DATE']) + df.at[i,'HOME']+df.at[i,'AWAY'] 
                
    return df    
    
def consolidate(df):
    
    df.sort_values(by=['ARTICLE_DATE'],axis=0,ascending=True,inplace=True)
    
    return df

def opendf(path):
    try:
        df = pd.read_pickle(path)
        return df
    except:
        return pd.DataFrame([])

def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

if __name__ == '__main__':
    df  = main()