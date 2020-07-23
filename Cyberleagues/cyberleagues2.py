import pandas as pd
import re,time,sqlite3
import numpy as np
from datetime import datetime, timedelta
from consolidate_data import consolidate_data
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup as BS


def main():
    
    browser = openBrowser(headless=True)
    browser.get('http://stats.cyberarena.live/results.aspx?tab=fifa')
    
    default_days_to_go_back = 100
    
    try:
        master = pd.read_pickle('master2.pkl')
        last_download_date = max(master['TIMESTAMP'].values)
        last_download_date = datetime.fromtimestamp(last_download_date)
        #go back an extra day
        last_download_date -= 24*3600
        stop_date = last_download_date.strftime('%Y-%m-%d')
    except:
        master = pd.DataFrame()
        last_download_date = datetime.now() - timedelta(days=default_days_to_go_back)
        stop_date = last_download_date.strftime('%Y-%m-%d')
        
    

    #get  the calendar object
    today =  datetime.now()
    
    for i in range(default_days_to_go_back):
        
        gamedate = today - timedelta(days=i)
        gamedate = gamedate.strftime('%Y-%m-%d')
        if gamedate == stop_date:
            print('Downloads up to date')
            break

        browser.execute_script(f"document.getElementsByName('tb_date')[0].setAttribute('value','{gamedate}')")    
        browser.execute_script(r"setTimeout('__doPostBack(\'tb_date\',\'\')', 0)")
    
        page = BS(browser.page_source,'html.parser')
        
        for table in page.find_all('table'):
            
            comp = table.find('caption')
            if comp:
                comp = comp.text.strip()
            else:
                comp = 'Unknown'
                               
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if not cols: continue
                
                gametime = cols[0].text
                
                try:
                    gameko = f'{gamedate} {gametime}'
                    timestamp = time.mktime(datetime.timetuple(datetime.strptime(gameko,'%Y-%m-%d %H:%M')))
                    timestamp = np.int64(timestamp)
                except ValueError:
                    continue
                
                try:
                    #Discard any 1st half data in case it accidentally gets parsed
                    score = cols[3].text.split('(')[0]
                    hscore,ascore = re.findall('[0-9]+',score)[:2]
                    hscore, ascore = [int(x) for x in [hscore,ascore]]
                except:
                    hscore = ascore = np.nan
                    
                hometeam = cols[2].text.strip()
                awayteam = cols[5].text.strip()
                
                gameID = str(timestamp)+hometeam+awayteam
                
                gamedic= {
                'DATE':[datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')],
                'TIMESTAMP':[timestamp],
                'COMPETITION':[comp],
                'HOME':[hometeam],
                'AWAY':[awayteam],
                'VENUE':[np.nan],
                'HOME SCORE':[hscore],
                'AWAY SCORE':[ascore],
                'TOTAL':[hscore+ascore],
                'GAME ID':[gameID],
                'STAGE':['Group Stage']
                           }
                                                                     
                #This turns the new game data into a pandas dataframe
                new_game = pd.DataFrame(gamedic)
                #This adds the new dataframe to the complete list of games
                master = pd.concat([master,new_game],ignore_index=True,sort=False)


    browser.close()
    master.drop_duplicates(subset='GAME ID',inplace=True,keep='last')

    master = consolidate_data(master)
                    
    master.to_pickle('master2.pkl')
    conn = connect_to_database('master2.db')
    master.to_sql('MATCHES',conn,index=False)
    conn.commit()
    conn.close()                    

def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

def openBrowser(headless=True):
    prefs = {"download.default_directory" : r"C:\Users\GerardArmstrong\Documents\GitHub\efootballresults\Cyberleagues"}
    chrome_options = Options()
    chrome_options.add_experimental_option("prefs",prefs)
    if headless == True:
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920x1080")
        print('Browser opening in headless mode')
    
    #Starts a new instance of Chrome using Selenium webdriver
    if not 'browser' in locals(): 
        browser = webdriver.Chrome(chrome_options=chrome_options,executable_path='C:\\Users\\GerardArmstrong\\Documents\\Python Scripts\\Compiler\\chromedriver.exe')

    return browser

def check_for_dupes(df,subset=['GAME ID','TOTAL']):
    #This function returns TRUE if the length of the original dataframe is not the same as the 
    #length of the same dataframe with dupes from subset column removed.
    
    #If the data frame is empty there are no dupes so just return false
    if df.empty: return False
    
    #Drop unplayed games as they should be allowed to be duped
    df.dropna(subset=['TOTAL'],inplace=True)
    if len(df) == 0: return False #If there is nothing in the dataframe yet there can't be any dupes - return false
    
    if all(x in list(df.keys()) for x in subset): #proceed if all the keys passed are in the dataframe
        dupes_exist = len(df.drop_duplicates(subset=subset,inplace=False,keep='last')) != len(df)
        if dupes_exist == True: print('Found duplicates')
    else:
        dupes_exist = False
        
    return dupes_exist


if __name__ == '__main__':
    main()
