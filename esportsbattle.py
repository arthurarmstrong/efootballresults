from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
import re
from bs4 import BeautifulSoup as BS
import pandas as pd
import sqlite3, dateparser
import numpy as np
import pickle
import sys,time
from datetime import datetime
sys.setrecursionlimit(200000)


def main(browser=None):
    
    conn = connect_to_database('esportsbattle.db')
    
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
    
    #this should not be needed anymore
    #input('Please log in and press any button to continue')
    
    #click all the buttons that say 'See More'
    browser, completed = click_seemore_buttons(browser)
    
    #save the page in case we want it again later
    pickle.dump(BS(browser.page_source,'html.parser'),open('page.pkl','wb'))
    
    if completed:
    
        #Use Beautiful Soup and Pandas to bring in the info
        df = get_results(browser)
        
        #Create date timestamps
        df = make_timestamps(df)
        
        #Send it to the database
        df.to_sql('MATCHES',conn,if_exists='replace',index=False)
        
        #Close up
        print ('Successfully completed.')
        conn.commit()
        conn.close()
        return browser, df
    
    else:
        print ('Did not complete clicking buttons. Browser has been returned so you may attempt to run again')
        conn.close()
        return browser, _
    
    #pickle.dump(browser.get_cookies(),open("../cookies.pkl","wb"))

def click_seemore_buttons(browser,count_limit=100):
    
    counter = 0
    
    try:
        while browser.find_elements_by_link_text('See More'):
            seemore = browser.find_elements_by_link_text('See More')
            for s in reversed(seemore):
                #This try exists as sometimes links are not clickable for whatever reason. That is fine, as they will be found
                # again in another pass
                try:
                    s.click()
                    counter += 1
                    if counter == count_limit:
                        print('Reached click count limit, returning')
                        return browser,True
                except: pass

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
        return gamedate[0]
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
    return homescore,awayscore

def get_teams(r):
    
    teams = re.findall('(?<=\().+?(?=\))',r.text)
    if len(teams) < 2:
        return False
    else:
        return teams[0:2]

def openBrowser(mode='Chrome',headless=True):
    
    browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')

    return browser

def get_cookies(browser):
    
    cookies = pickle.load(open("../cookies.pkl", "rb"))
    for cookie in cookies:
        browser.add_cookie(cookie)
        
def make_timestamps(df):
    
    for i in df.index.values:
        date = ' '.join([df.at[i,'GAME_DATE'],df.at[i,'TIME']])
        df.at[i,'DATE'] = np.int64(time.mktime(datetime.timetuple(datetime.strptime(date,'%d.%m.%Y %H:%M'))))
        
    return df    
    
def connect_to_database(path):
    try:
        open(path).close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

if __name__ == '__main__':
    browser,df  = main()