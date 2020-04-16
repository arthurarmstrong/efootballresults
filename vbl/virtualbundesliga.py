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

class Team:
    
    def __init__(self,name):
        self.name = name
        
class Player:
    
    def __init__(self,name,status=None):
        username = re.findall('\".*\"',name)
        if username:
            self.name = name.replace(username[0],'').replace('  ',' ').strip()
            self.username = username[0].replace('"','')
            
            pros = opendf('pros')
            if pros.empty:
                pros = pros.append({'Username':self.username,'Real Name':self.name},ignore_index=True)
                pros.to_pickle('pros')    
            else:
                if not self.name in pros['Real Name'].values:
                    pros = pros.append({'Username':self.username,'Real Name':self.name},ignore_index=True)
                    pros.to_pickle('pros')    
            del pros
                
        else:
            self.name = name
            self.username = 'Unknown'
        
        #if not status:
        #    self.status = input(f'Please state whether {name} is a pro or amateur. Pro? (y/n): ')
        #else:
        #    self.status = status
        
class Match:
    
    def __init__(self,home,away,homescore,awayscore,homeplayingas,awayplayingas,href=None,console=None,date=None,stage='Group Stage'):
        self.home = home
        self.away = away
        self.homescore = homescore
        self.awayscore = awayscore
        self.homeplayingas = homeplayingas
        self.awayplayingas = awayplayingas
        self.console = console
        self.datestr = date
        self.href = href
        self.stage = stage
        
        if self.datestr:
            self.make_timestamp()
        
    def get_match_date(self):
        
        #Check to see if the url was visited already
        if self.href in visitedlist.keys():
            self.datestr = visitedlist[self.href]
            self.make_timestamp()
        else:
            browser.get(self.href)
            while True:
                try:
                    page = BS(browser.page_source,'html.parser')
                    header = page.find('div',{'class':'m03__header__meta'})
                    self.datestr = header.find('span').text
                    
                    #Just required until the first full scan is done. Then another method will be required
                    visitedlist[self.href] = self.datestr
                    self.make_timestamp()
                    break
                except:
                    pass
            
    def make_timestamp(self):
        date = dateparser.parse(self.datestr,settings={'DATE_ORDER':'DMY'})
        self.time_stamp = np.int64(time.mktime(date.utctimetuple()))
        
    def to_df(self):
        df = {'DATE':[self.time_stamp],'HOME':[self.home],'AWAY':[self.away],'HOME PLAYING AS':[self.homeplayingas],
              'AWAY PLAYING AS':[self.awayplayingas],'HOME SCORE':[self.homescore],'AWAY SCORE':[self.awayscore],'CONSOLE':[self.console],'GAME ID':[str(self.time_stamp)+self.home+self.away],'STAGE':self.stage}
        df = pd.DataFrame(data=df)
        
        return df
                
def updatevbl(browser=None):
    
    df = opendf('virtualbundesliga')
    
    browser.get('https://virtual.bundesliga.com/en/club-championship/clubs')
    page = BS(browser.page_source,'html.parser')
    
    while not page.find('a',{'class':'club__panel'}):
        time.sleep(4)
        print('Waiting for clubs page to load..')
        page = BS(browser.page_source,'html.parser')
    
    #build the list of teams
    teamlist = page.find('ethlete-tournament-public-participant-list').find_all('a',{'class':'club__panel'})
    teams = set()
    players =  set()
    for team in teamlist:
        new_team = Team(team.find('img').get('alt'))
        new_team.href = 'https://virtual.bundesliga.com/de'+team.get('href')
        teams.add(new_team)
    
    #loop through all the teams
    for team in teams:
        print (team.href)
        browser.get(team.href)
        page = BS(browser.page_source,'html.parser')
        
        while not page.find('a',{'class':'player__panel'}):
            time.sleep(5)
            print('Waiting for team page to load..')
            page = BS(browser.page_source,'html.parser')
            
        for player_card in page.find_all('a',{'class':'player__panel'}):
            new_player = Player(player_card.get('title'),'Pro')
            new_player.href = 'https://virtual.bundesliga.com/de'+player_card.get('href')
            players.add(new_player)
            
    for player in players:
        player.matches = set()
        
        browser.get(player.href)
        page = BS(browser.page_source,'html.parser')
        tries = 0
        while not page.find('span',{'class':'matchday__result__score'}):
            time.sleep(3)
            print('Waiting for player page to load..')
            tries +=1
            if tries >= 10: break
            page = BS(browser.page_source,'html.parser')
            
        for card in page.find_all('div',{'class':'matchdays'}):
            homeplayingas, awayplayingas = card.find('h5').find('span').text.split(' vs. ') 
            for match in card.find_all('a',{'class':'matchday__result'}):
                homeaway  = match.find_all('span')[1].text
                console = match.find_all('strong')[-1].text.replace('vs.','').strip()
                homeaway = homeaway.replace(console,'').strip()
                hometeam, awayteam = [x.strip(',').strip() for x in homeaway.split('vs.')]
                homescore, awayscore = [x for x in match.find('span',{'class':'matchday__result__score'}).text.split(':')]
                
                href = 'https://virtual.bundesliga.com/de'+match.get('href')
                player.matches.add(Match(hometeam,awayteam,homescore,awayscore,homeplayingas,awayplayingas,href,console))
            
    #scan through all the matches downloaded and get their dates        
    for p in players:
        for m in p.matches:
            m.get_match_date()
            
    #update the dataframe
    for p in players:
        for m in p.matches:
            new_match = m.to_df()
            df = pd.concat([new_match,df],ignore_index=True,sort=False)
            df.drop_duplicates(subset=['GAME ID'],inplace=True)
            df.to_pickle('virtualbundesliga')
                
    return df

def get_home_challenge_matches(url='https://virtual.bundesliga.com/en/bundesliga-home-challenge'):
    
    browser.get(url)
    existing_matches = opendf('virtualbundesliga')
    
    matches = []
    
    page = BS(browser.page_source,'html.parser')
    
    while not page.find_all('div',{'class':'m02__match-games__match-game'}):
        time.sleep(2)
        page = BS(browser.page_source,'html.parser')
    
    #each matchday has a group
    for matchdategroup in page.find_all('div',{'class':'m02__match-group'}):
        matchdate = matchdategroup.find('h3').text
        
        #each match
        for match in matchdategroup.find_all('div',{'class':'m02__match'}):
            matchtime = match.parent.find('div',{'class':'m02__match__round'}).text
            homeplayingas,awayplayingas  = [x.text for x in match.find_all('div',{'class':'m02__match__opponent__name'})]
            print(matchdate,matchtime,homeplayingas,awayplayingas)
            
            #each game within a match
            for game in match.parent.find_all('div',{'class':'m02__match-games__match-game'}):
                hometeam,awayteam = [x.text for x in game.find_all('div',{'class':'m02__match-games__match-game__opponent__name'})]
                home = Player(hometeam)
                away = Player(awayteam)
                hometeam = home.name
                awayteam = away.name
                
                try:
                    homescore,awayscore= [int(x.text.strip()) for x in game.find_all('div',{'class':'m01__match__data m01__match__data--points'})]
                except:
                    homescore = awayscore = np.nan
                console = "PS4"
                
                matches.append(Match(hometeam,awayteam,homescore,awayscore,homeplayingas,awayplayingas,None,console,matchdate+' '+matchtime,stage='Bundesliga Home Challenge'))
    
    for m in matches:
        new_match = m.to_df()
        existing_matches = pd.concat([existing_matches,new_match],ignore_index=True,sort=False)
        
    existing_matches = set_status(existing_matches)
    
    return existing_matches
    
def main(browser=None):
    
    conn = connect_to_database('virtualbundesliga.db')
    c = conn.cursor()
    df = opendf('virtualbundesliga')
    
    #get an instance of chrome going
    if not browser:
        browser =  openBrowser(headless=False)
    else:
        pass

    for i in range(1,22):
        browser.get('https://virtual.bundesliga.com/en/club-championship/spieltage/'+str(i))
        
        #Use Beautiful Soup and Pandas to bring in the info
        new_results = get_results(browser)
        df = pd.concat([new_results,df],ignore_index=True,sort=False)
        print (df)
        
    #Create date timestamps
    df = make_timestamps(df)
    
    #look for values that should be cansolidated
    df = consolidate_data(df)
    df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
    
    #Send it to the database
    df.to_sql('MATCHES',conn,if_exists='replace',index=False)
    df.to_pickle('virtualbundesliga')
    
    #Close up
    print ('Successfully completed.')
    conn.commit()
    conn.close()
    browser.close()
    return df

def get_results(browser):
    
    games = []
    page  = BS(browser.page_source,'html.parser')
    
    #wait for elements to load
    while not page.find('div',{'class':'m02__match'}):
        print('No matches found. Waiting for them to load..')
        time.sleep(2)
        page  = BS(browser.page_source,'html.parser')

    
    for match in page.find_all('div',{'class':'m02__match'}):
        
            gamedate = get_game_date(match)
            
            teams = get_teams(match)
            if not teams:
                print('Problem getting team names')
                continue
            hometeam,awayteam = teams
        
            homescore, awayscore = get_score(match)
            
            #Turn these returned values into a dictionary and append to the list of games
            games.append({'GAME_DATE':gamedate, 'HOME':hometeam,'AWAY':awayteam,'HOME SCORE':homescore,'AWAY SCORE':awayscore,'STAGE':'Group Stage'})

        
    df = pd.DataFrame(data=games)
    return df

def get_game_date(match):
    
    gamedate = match.find('div',{'class':'m02__match__round'}).text
    gamedate = re.findall('[0-9]{2}\.[0-9]{2}\.[0-9]{4}, [0-9]+:[0-9]+',gamedate)[0]
    
    return gamedate
    
def get_playing_as(r):
    spl = r.text.split(' - ')
    try:
        home = re.findall(' .*\(',spl[0])[0]
        home = home.strip()[:-1]
        away = spl[1][:spl[1].find('(')].strip()
    except:
        return None, None
    
    return home, away
                
    
def get_score(match):
    
    score = match.find('div',{'class':'m01__games__game'})
    
    if not score:
        return np.nan,np.nan
    else:
        homescore, awayscore = [x for x in score.text.split(':')]
        return int(homescore),int(awayscore)

def get_teams(match):
    
    teams = match.find_all('div',{'class':'m02__match__opponent__name'})
    if len(teams) != 2:
        return False
    else:
        return [x.text for x in teams]

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
        date = df.at[i,'GAME_DATE']
        unix_time_stamp = np.int64(time.mktime(datetime.timetuple(datetime.strptime(date,'%d.%m.%Y, %H:%M'))))
        df.at[i,'DATE'] = datetime.fromtimestamp(unix_time_stamp).strftime('%Y-%m-%d %H:%M')
        df.at[i,'GAME ID'] = str(df.at[i,'DATE']) + df.at[i,'HOME']+df.at[i,'AWAY'] 
                
    return df    
    
def consolidate(df):
    
    df.sort_values(by=['ARTICLE_DATE'],axis=0,ascending=True,inplace=True)
    
    return df

def opendf(df):
    if df in os.listdir():
        return pd.read_pickle(df)
    else:
        return pd.DataFrame([])

def connect_to_database(path):
    try:
        open(path,'w').close()
    except:
        pass

    conn = sqlite3.connect(path)
    
    return conn

def set_status(df):
    pros = opendf('pros')
    for i in df.index.values:
        
        status = 'Amateur'
        for p in pros['Username'].values:
            if 'HOME USERNAME' in df.loc[i].keys():
                try:
                    if p in df.at[i,'HOME USERNAME']:
                        status = 'Pro'
                        break
                except: pass
        df.at[i,'HOME STATUS'] = status
            
        status = 'Amateur'
        for p in pros['Username'].values:
            if 'AWAY USERNAME' in df.loc[i].keys():
                try:
                    if p in df.at[i,'AWAY USERNAME']:
                        status = 'Pro'
                        break
                except: pass
        df.at[i,'AWAY STATUS'] = status
        
        #if df.at[i,'HOME USERNAME'] in pros['Username'].values or df.at[i,'HOME'] in pros['Real Name'].values:
            #df.at[i,'HOME STATUS'] = 'Pro'
        #else:
        #    df.at[i,'HOME STATUS'] = 'Amateur'
        #if df.at[i,'AWAY USERNAME'] in pros['Username'].values or df.at[i,'AWAY'] in pros['Real Name'].values:
        #    df.at[i,'AWAY STATUS'] = 'Pro'
        #else:
        #    df.at[i,'AWAY STATUS'] = 'Amateur'
        
    return df
            
def usernames_to_names(df):
    
    pros = opendf('pros')
    
    pro_usernames = pros['Username'].values
    pro_realnames = pros['Real Name'].values
    
    #for each row in dataframe
    for i in df.index.values:
        
        thisuname = df.loc[i,'HOME']
        
        #get a list of all players, could be one or two
        homeplayers = [x.strip() for x in thisuname.split(',')]
        #iterate over all players
        for player in homeplayers:            
            
            #if the name is found in the file of pro players usernames, it needs converting to their real name
            if player in pro_usernames:
                #get a df slice with the username and name
                pro = pros[pros['Username']==player]
                #the pro is a DF series so we need to iterate over each match
                for j in pro.index:
                    #get the real name
                    real_name = pro.at[j,'Real Name']
                    #replace the username with the real name
                    df.at[i,'HOME'] = df.at[i,'HOME'].replace(player,real_name)
                    #move username to the home username column
                    df.at[i,'HOME USERNAME'] = thisuname
                    
            if player in pro_realnames:
                index = pros[pros['Real Name']==player].index.values[0]
                df.at[i,'HOME USERNAME'] = thisuname.replace(player,pros.at[index,'Username'])

        
        #do the same for away column                    
        thisuname = df.loc[i,'AWAY']
        awayplayers = [x.strip() for x in thisuname.split(',')]
        for player in awayplayers:            

            if player in pros['Username'].values:
                #get a df slice with the username and name
                pro = pros[pros['Username']==player]
                for j in pro.index:
                    real_name = pro.at[j,'Real Name']
                    df.at[i,'AWAY'] = df.at[i,'AWAY'].replace(player,real_name)
                    df.at[i,'AWAY USERNAME'] = thisuname

            if player in pro_realnames:
                index = pros[pros['Real Name']==player].index.values[0]
                df.at[i,'AWAY USERNAME'] = thisuname.replace(player,pros.at[index,'Username'])

    return df

def build_table(df,season=None):

    unique_players = set()
    for team, players in teams.items():
        for player in players:
            unique_players.add(player)
    
    #Remove duplicates
    df.drop_duplicates(subset=['DATE','HOME','AWAY','HOME SCORE','AWAY SCORE'],inplace=True,keep='last')
    df.dropna(subset=['HOME SCORE','AWAY SCORE'],inplace=True)
    #Build zero vector to populate table with initially
    zero_column = np.zeros(len(players),dtype=int)
    #Initialise dataframe
    table = pd.DataFrame(index=teams,data={'P':zero_column,'W':zero_column,'D':zero_column,'L':zero_column,'F':zero_column,'A':zero_column,'+/-':zero_column,'Pts':zero_column,'GD Per Game':zero_column})
  
    
    for i in df.index:
        this_game = df.loc[i]
        
        h_s = int(this_game['HOME SCORE'])
        a_s = int(this_game['AWAY SCORE'])
        if h_s == a_s:
            points = [1,1]
            table.at[this_game['HOME'],'D'] += 1
            table.at[this_game['AWAY'],'D'] += 1
        if h_s > a_s:
            points = [3,0]
            table.at[this_game['HOME'],'W'] += 1
            table.at[this_game['AWAY'],'L'] += 1            
        if h_s < a_s:
            points = [0,3]
            table.at[this_game['HOME'],'L'] += 1
            table.at[this_game['AWAY'],'W'] += 1
        
        for player in unique_players():
            table.at[this_game['HOME'],'P'] += 1
            table.at[this_game['HOME'],'F'] += int(this_game['HOME SCORE'])
            table.at[this_game['HOME'],'A'] += int(this_game['AWAY SCORE'])
            table.at[this_game['HOME'],'Pts'] += points[0]
            table.at[this_game['HOME'],'+/-'] += h_s-a_s
            table.at[this_game['AWAY'],'P'] += 1
            table.at[this_game['AWAY'],'F'] += int(this_game['AWAY SCORE'])
            table.at[this_game['AWAY'],'A'] += int(this_game['HOME SCORE'])
            table.at[this_game['AWAY'],'Pts'] += points[1]
            table.at[this_game['AWAY'],'+/-'] += a_s-h_s
        
    table['GD Per Game'] = (table['F']-table['A'])/table['P']
    table = table.round(2)
    
    table.sort_values(by=['GD Per Game'],ascending=False,inplace=True)

    return table

if __name__ == '__main__':
        
    df = df2 = pd.DataFrame()
    
    #get an instance of chrome going
    browser =  openBrowser(headless=False)

    
    visitedlist = pickle.load(open('urlmaptogamedate','rb'))
    
    #df  = updatevbl(browser)
    #try:
    home_chal = get_home_challenge_matches()
    for wk in range(1,4):
        home_chal_wk = get_home_challenge_matches(f'https://virtual.bundesliga.com/de/bundesliga-home-challenge/spieltag/{wk}')
        home_chal = pd.concat([home_chal,home_chal_wk],ignore_index=True,sort=False)
    #except:
    #    print("Didn't get home challenge")
    
    df3 = pd.concat([df,home_chal],ignore_index=True,sort=False)
    df3.drop_duplicates(subset='GAME ID',inplace=True,keep='last')
    df3 = usernames_to_names(df3)
    df3 = set_status(df3)
    
    #format dates for the database to read
    for i in df3.index.values:
        try:
            unix_time_stamp = df3.at[i,'DATE']
            df3.at[i,'TIMESTAMP'] = unix_time_stamp
            df3.at[i,'DATE'] = datetime.fromtimestamp(unix_time_stamp)
        except:
            pass
    
    conn = connect_to_database('virtualbundesliga.db')
    
    df3.to_pickle('virtualbundesliga')
    df3.to_sql('MATCHES',conn,index=False)
    
    conn.commit()
    conn.close()
    pickle.dump(visitedlist,open('urlmaptogamedate','wb'))
    