#Selenium is the library I use for web scraping
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
#regex is for parsing data based on string patterns. os is for traversing directories on the computer
import re,os
#bs4/beautifulsoup is used to parse html documents
from bs4 import BeautifulSoup as BS
#pandas is basically a python version of excel
import pandas as pd
#sqlite3 is for sql databases. dateparser is used to take a date string that can be in any format e.g. dd/mm/yyyy mm/dd/yyyy and convert it to a timestamp
import sqlite3, dateparser
import numpy as np
import sys,time
from datetime import datetime

def main():

    #this checks to see whether you have a selenium browser open. if you do it uses that, if you don't it creates one
    #you need to downloaded chromedriver.exe and change the path to your directory
    if not 'browser' in locals(): 
        browser = webdriver.Chrome(executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')
    
    
    #this takes the browser to specified url
    browser.get(f'http://e.ligamx.net/cancha/partidos')
    
    #get the web pages current html and store it as a beautiful soup object
    page = BS(browser.page_source,'html.parser')
    
    #keep running until i say stop
    while True:
        page=BS(browser.page_source,'html.parser')
        #in the html document 'page', find the first 'ul' element that has class 'selector-matches'
        if page.find('ul',{'class':'selector-matches'}):
            #if the element i'm looking for is found, the page must be fully loaded, so you can break out of the while loop and proceed
            if page.find('ul',{'class':'selector-matches'}).text: break

    #get the competition name        
    comp = page.find('div',{'id':'subMail'}).text
    #get the season year
    season = re.findall('[0-9]{4}\-*[0-9]*',comp)[0].strip()
    #get rid of the season from the competition name
    comp = comp.split(' / ')[0].strip()

    stage = 'Group Stage'
    
    #look for a pandas file that follows the variable formatted string. if it doesnt exist, give me an empty dataframe
    existing_games = opendf(f'eligamx-{comp}')  
    
    #from the browser, return all the element that has the class name 'selector-matches', and from it, get all of its 'li' elements, then store their 'data-nojnda' attribute in an array
    matchdays = [x.get_attribute('data-nojnda') for x in browser.find_element_by_class_name('selector-matches').find_elements_by_tag_name('li')]
    
    #loop  through each of those stored matchday elements
    for matchday in matchdays:
        
        #find the button corresponding to that data-nojnda element. if you do not do this, selenium will return a stale element exception error
        #click the matchday button
        [x for x in browser.find_element_by_class_name('selector-matches').find_elements_by_tag_name('li') if x.get_attribute('data-nojnda') == matchday][0].click()
    
        #save the current html page source as a beautiful soup object
        page = BS(browser.page_source,'html.parser')
    
        #get all of the div elements with class 'cntPrtdo' and loop through them
        for row in page.find_all('div',{'class':'cntPrtdo'}):
                   
            #sometimes a row will not have the data we are looking for. in that case, it is probably not a game.
            #for that reason we can do a try/except where when an error occurs, we just move on to the next element
            try:
                #find the date. it only has day and month, so add 2020 to it. also append the time to it
                datestr = row.find('span',{'class':'date'}).text+'/2020 '+row.find('span',{'class':'hour'}).text
                #get rid of the 'hr' part of the string. dateparser had trouble getting the right date when this was left in
                datestr = datestr.replace('hr','').strip()
                #changed the dateparser time tuple object into a utc time tuple
                datetimetuple = dateparser.parse(datestr,settings={'DATE_ORDER': 'DMY'}).utctimetuple()
                #turn the utc time tuple into a unix timestamp
                time_stamp = np.int64(time.mktime(datetimetuple))
                #correct for timezone
                #correct to uk timezone
                time_stamp += 6*3600
            except:
                continue
            
            #now we try and find team names
            try:
                #get the href with the team names in it
                #this finds the hyperlink that points to the game page. it has team names in the link so that we dont need to actually visit the page
                h = row.findNext('div',{'class':'sub-menu'}).findNext('ul',{'class':'nacionalMarcador'}).find('a').get('href')
                #use re patterns to find the home and away team names, strip out the unnecessary parts
                awayteam = ' '.join([x.capitalize() for x in re.findall('-vs-.*-jornada',h)[0].replace('-vs-','').replace('-jornada','').replace('-',' ').split(' ')])
                hometeam = ' '.join([x.capitalize() for x in re.findall('a-minuto-.*-vs',h)[0].replace('a-minuto-','').replace('-vs','').replace('-',' ').split(' ')])
                #create a unique game id
                gameid = str(time_stamp)+hometeam+awayteam
            except:
                continue
        
            try:
                #find the result. if there isn't one, it will return an error and we will get np.nan, which is fine for unplayed games
                homescore,awayscore = [int(x) for x in re.findall('[0-9]+',row.find('div',{'class':'score'}).text)[:2]]
                print(homescore,awayscore)
            except:
                homescore = awayscore = np.nan
            
            #get the venue. if there is no element found for the given tag and class, venue will be None, and will return np.nan
            #if the element is found, it will return venue.text (the element's text attribute)
            venue = row.find('span',{'class':'stadium'})
            if venue:
                venue = venue.text
            else:
                venue = np.nan
            
            #Store all the data for this game in a dictionary that will be used to populate the pandas dataframe
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
        
    #running this script over and over will download the same games multiple times, so we need to drop the duplicates
    existing_games.drop_duplicates(subset=['GAME ID'],inplace=True,keep='last')
    
    #create a connection to an sql database
    conn = connect_to_database(f'eligamx-{comp}.db')
    #store the pandas file so that we can open it again later on using the opendf function
    existing_games.to_pickle(f'eligamx-{comp}')
    #also store as a sql database that is used for the website to query
    existing_games.to_sql('MATCHES',conn,index=False)
    #save changes to db
    conn.commit()
    #close db
    conn.close()
    #close the selenium browser
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
