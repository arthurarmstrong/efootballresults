import pandas as pd
import re,dateparser,time,sqlite3,os
import numpy as np
from datetime import datetime
from consolidate_data import consolidate_data
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def main():
    
    #Delete the old sheet
    if 'Results .xlsx' in os.listdir():
        os.remove('Results .xlsx')
    
    #Download the new sheet
    browser = openBrowser(headless=False)
    browser.get('https://docs.google.com/spreadsheets/d/1DzPBoZzRx1JraO48IaiRsTCML75XXLFMj0ZItfaI8-A/edit#gid=473368820')
    browser.find_element_by_id('docs-file-menu').click()
    time.sleep(2)
    [x for x in browser.find_elements_by_tag_name('span') if '다운로드' in x.text][0].click()
    time.sleep(2)
    [x for x in browser.find_elements_by_tag_name('span') if 'xlsx' in x.text][0].click()
    
    #Wait until sheet downloaded
    while not 'Results .xlsx' in os.listdir():
        time.sleep(5)
    browser.close()
    
    Excel = pd.ExcelFile(r'Results .xlsx')

    master = pd.DataFrame()

    for sheet_num in range(len(Excel.sheet_names)):
        df = pd.read_excel(Excel,sheet_num,header=None)
        fixtures_date = Excel.sheet_names[sheet_num]
        
        for i in df.index.values:
            
            row = df.loc[i]
            
            #Set the current competition if necessary
            try:
                compheader = re.findall('[0-9]+:[0-9]+ - [0-9]+:[0-9]+',row[1])
                if compheader:
                    compheader = compheader[0]
                    comp = row[1].replace(compheader,'').strip()
                    fixtures_start = re.findall('[0-9]+:[0-9]+',row[1])[0]    
                    fixtures_start = fixtures_date + ' ' + fixtures_start
                    datetimetuple = dateparser.parse(fixtures_start).utctimetuple() 
                    timestamp = np.int64(time.mktime(datetimetuple))
                    
                    gamescounted = 0
            except:
                continue
            
            #if type(row[4]) == float:
                #if np.isnan(row[4]): continue
        
            try:
                if 'channel' in row[4]:         
                    
                    hometeam = re.findall('\(.*\)',row[1])[0].strip('()')
                    awayteam = re.findall('\(.*\)',row[3])[0].strip('()')
                    
                    try:
                        #Discard any 1st half data in case it accidentally gets parsed
                        score = row[2].split('(')[0]
                        hscore,ascore = re.findall('[0-9]+',score)[:2]
                    except:
                        hscore = ascore = np.nan
        
                    #a bit of a hacky solution to try and get more accurate game times
                    gamescounted += 1
                    if gamescounted %2 == 0:
                        timestamp += 60*15
                        
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
            except:
                continue

    master.drop_duplicates(subset='GAME ID',inplace=True,keep='last')
                    
    master.to_pickle('master.pkl')
    conn = connect_to_database('master.db')
    master.to_sql('MATCHES',conn,index=False)
    conn.commit()
    conn.close()                    
    
    #Group by competitions for saving separately
    for comp in master.groupby('COMPETITION'):
        d = pd.DataFrame(comp[1])
        d.to_pickle(comp[0])
        conn = connect_to_database(comp[0])
        d.to_sql('MATCHES',conn,index=False)
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


if __name__ == '__main__':
    main()
