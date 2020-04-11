import pandas as pd
import re,dateparser,time,sqlite3
import numpy as np
from datetime import datetime
from consolidate_data import consolidate_data

def main():
    
    Excel = pd.ExcelFile(r'Results .xlsx')

    master = pd.DataFrame()

    for sheet_num in range(len(Excel.sheet_names)):
        df = pd.read_excel(Excel,sheet_num,header=None)
        fixtures_date = Excel.sheet_names[sheet_num]
        
        for i in df.index.values:
            
            row = df.loc[i]
            
            is_fixture = False
            is_competition_header = False   
            
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
                    is_fixture = True            
                    
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
                        timestamp += 60*18
                        
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
    for comp in df.groupby('COMPETITION'):
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

if __name__ == '__main__':
    main()
