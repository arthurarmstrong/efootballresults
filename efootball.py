import sqlite3,time
import pandas as pd
import numpy as np
from scipy import stats
from flask import Flask, flash, redirect, render_template, request, session, abort
import os

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SECRET_KEY'] = os.urandom(12)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return render_template('home.html')

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'eFootball' and request.form['username'] == 'bet365':
        session['logged_in'] = True
    else:
        flash('wrong password!')
    
    return home()

@app.route('/getgames.php')
def getgames():

    days = request.args.get('days')
    searchstr = request.args.get('search')
    comp = request.args.get('comp')
    teams = request.args.get('teams')

    if not searchstr == 'None':
        searchfilter = " AND (HOME || AWAY) LIKE '%"+searchstr+"%'"
        labelsuffix = ' for search "'+searchstr+'".'
    else:
        searchfilter = ''
        labelsuffix = ''
        
    if not teams == 'None':
        teamlen = len(teams.split(','))
        if teamlen == 1:
            teamfilter = " AND (HOME IN ("+teams+") OR AWAY IN ("+teams+"))"
        else:
            teamfilter = ' AND (HOME IN ('+teams+') AND AWAY IN ('+teams+'))'
    else:
        teamfilter = ''
    
    finalsheader= 'Finals Games'
    datefilter = "strftime('%s',DATE) > strftime('%s','now','-"+days+" days')"
    #datefilter = "strftime('%s', DATE) BETWEEN strftime('%s','now','-"+days+" days') AND strftime('%s','now')"
    query = """SELECT DATE, HOME, AWAY, 
            CAST("HOME SCORE" AS INTEGER) AS "HOME SCORE",
            CAST("AWAY SCORE" AS INTEGER) AS "AWAY SCORE", 
            STAGE,
            CAST(strftime("%s",DATE) AS INTEGER) AS TIMESTAMP
            FROM MATCHES
            WHERE ("""+datefilter + searchfilter + teamfilter + """ AND HOME NOT LIKE "%,%")
            ORDER BY DATE DESC"""
    
    if comp == '1':
        dbpath = './eFootball/efootball.db'
        #datefilter = "strftime('%s',DATE) BETWEEN strftime('%s','now','-"+days+" days') AND strftime('%s','now')"
    elif comp == '2':
        dbpath = './eSportsBattle/esportsbattle.db'
        #query = 'SELECT DATE, HOME, AWAY, "HOME SCORE", "AWAY SCORE", STAGE FROM MATCHES WHERE ('+datefilter + searchfilter + ') ORDER BY DATE DESC'
    elif comp =='3':
        dbpath = './vbl/virtualbundesliga.db'
        finalsheader = 'Bundesliga Home Challenge'
        #query = 'SELECT DATE, HOME || " (" || "HOME STATUS" || ")" AS HOME, AWAY || " (" || "AWAY STATUS" || ")" AS AWAY, "HOME SCORE", "AWAY SCORE", STAGE FROM MATCHES WHERE ('+datefilter + searchfilter + ' AND CONSOLE="PS4") ORDER BY DATE DESC'    
        query = query.replace('AS TIMESTAMP', 'AS TIMESTAMP, "HOME STATUS", "AWAY STATUS"')
        #query = query.replace('AND HOME NOT LIKE "%,%"','AND HOME NOT LIKE "%,%" AND CONSOLE="PS4"')
    elif comp =='4':
        dbpath = './FUFV/Primera Division FUFV.db'
    elif comp =='5':
        dbpath = './FUFV/Segunda Division FUFV.db'
    elif comp =='6':
        dbpath = './FUFV/Tercera Division FUFV.db'
    elif comp =='7':
        dbpath = './eligamx/eligamx-Torneo de eLiga MX.db'
    elif comp =='8':
        dbpath = './Cyberleagues/master2.db'
    elif comp =='9':
        dbpath = './BR/Electronic LeaguesPro Player Cup - PS4.db'
    elif comp =='10':
        dbpath = './BR/Electronic LeaguesPro Player Cup - XBox.db'
    elif comp =='11':
        dbpath = './futhead_tnf/TNF.db'
    elif comp =='12':
        dbpath = './GT Leagues/GT.db'
    elif comp =='13':
        dbpath = 'FUFV/Primera Division.db'
    elif comp =='14':
        dbpath = 'FUFV/Segunda Division.db'
    elif comp =='15':
        dbpath = 'FUFV/Tercera Division.db'
    elif comp =='16':
        dbpath = './BR/Electronic LeagueseSports Battle.db'
    else:
        return ''
    
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    #Get the selected match data
    c.execute(query)   
    resp = c.fetchall()

    #Get the over under data
    gamestonow = [x for x in resp if x[6] < time.time()]
    totalover = 0
    gamecount = 0
    drawcount = 1
    for g in gamestonow:
        if type(g[3])==int:
            if g[3]+g[4] > 2:
                totalover += 1
            gamecount += 1
            
            if g[3]==g[4]:
                drawcount += 1

    #Get total stats
    gamecount = len(gamestonow)
    if gamecount == 0:
        overperc = np.nan
    else:
        overperc = round(totalover*100/gamecount,1)
    underperc = round(100-overperc,1)

    #Get draw statsif gamecount == 0:
    if gamecount == 0:
        drawperc = np.nan
    else:
        drawperc = round(drawcount*100/gamecount,1)
    

    responsetext = ''
    
    if resp:

        responsetext += '<div id="overunder" class="text-center"><table class="table table-bordered table-striped"><th colspan="2">Overall Stats'+labelsuffix+'</th><tr><td>Games</td><td>'+str(gamecount)+'</td></tr><tr><td>Over</td><td>'+str(totalover)+' ('+str(overperc)+'%)</td></tr><tr><td>Under</td><td>'+str(gamecount-totalover)+' ('+str(underperc)+'%)</td></tr><tr><td>Draws</td><td>'+str(drawcount)+' ('+str(drawperc)+'%)</td></tr></table></div><p>'
        
        #Turn the results into a pandas file
        table = pd.read_sql_query(query,conn)
        #Build a table of the group games
        #try:
        responsetext += '<div id="ladder" class="text-center center-block"><h2>Table - Group Games</h2><p>'
        grouptable = build_table(table[table['STAGE']=='Group Stage'])
        responsetext += grouptable.to_html() + '</div><p>'
        #except:
        #    pass
        try:
            #Make a new header for the finals table
            responsetext += f'<h2>Table - {finalsheader}</h2><p><div id="finalsladder" class="text-center center-block">'
            #Build a table of the finals games
            finaltable = build_table(table[table['STAGE']!='Group Stage'])
            responsetext += finaltable.to_html() + '</div><p>'
        except:
            #sometime the finals table won't exist so the table won't generate. It needs to be closed properlu
            responsetext += '</div><p>'
        
        #Build the table of individual games
        responsetext +='<table class="table table-dark table-bordered table-striped" id="gamestable"><tr><th onclick="sortTable(0)">Date</th><th onclick="sortTable(1)">Home</th><th onclick="sortTable(2)">Away</th><th onclick="sortTable(3)">Home Score</th><th onclick="sortTable(4)">Away Score</th></tr>'
        
        for r in resp:
            #Round scores
            if not r[3] == None:
                r = (r[0],r[1],r[2],r[3],r[4])
            else:
                r = (r[0],r[1],r[2],'-','-')
            #Add row
            responsetext += '<tr><td>'+str(r[0])+'</td><td>'+str(r[1])+'</td><td>'+str(r[2])+'</td><td>'+str(r[3])+'</td><td>'+str(r[4])+'</td></tr>'
    
    
        responsetext += '</table></div>'
    
    conn.close()    
        
    return responsetext


@app.route('/getdbupdatetime.php')
def getdbupdatetime():
    
    updatetime = os.path.getmtime('eFootball/efootball.db') 
    return str(updatetime)

def build_table(df,season=None):

    class Median:
        def __init__(self,ls):
            self.data = {}
            #initialise each team with an empty list
            for i in ls:
                self.data[i] = []
            
        def insert(self,player,val):
                self.data[player].append(val)

        def calc_medians(self):
            self.medians = {}
            for player in self.data.keys():
                self.medians[player] = np.median(self.data[player])
 
    
    #Build table of unique teams
    teams = get_unique_values_from_column(df,['HOME','AWAY'])
    #Remove duplicates
    df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
    df.dropna(subset=['HOME SCORE','AWAY SCORE'],inplace=True)
    #Build zero vector to populate table with initially
    zero_column = np.zeros(len(teams),dtype=int)
    #Initialise dataframe
    table = pd.DataFrame(index=teams,data={'P':zero_column,'W':zero_column,'D':zero_column,'L':zero_column,'F':zero_column,'A':zero_column,'+/-':zero_column,'Pts':zero_column,'GD Per Game':zero_column,'Win %':zero_column,'Rating':zero_column})
  
    median = Median(teams)
    
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
        
        median.insert(this_game['HOME'],h_s-a_s)
        median.insert(this_game['AWAY'],a_s-h_s)
        
    table['GD Per Game'] = (table['F']-table['A'])/table['P']
    
    
    table['Win %'] = (table['W']/table['P'])*100
    
    #do some work on the medians
    median.calc_medians()
    
    #Also provide a combined GD using win % as a regressor
    xs = table['Win %'].dropna().values
    ys = table['GD Per Game'].dropna().values
    
    
    slope, intercept, _, _, _ = stats.linregress(xs,ys)
    table['Rating'] = (table['GD Per Game']+(table['Win %']*slope+intercept))/2
    
    #include medians in the rating
    for team in teams:
        table.at[team,'Rating'] = (table.at[team,'Rating'] + median.medians[team]) / 2

    
    table = table.round(2)
    
    table.sort_values(by=['Rating'],ascending=False,inplace=True)

    return table

def get_unique_values_from_column(df,cols):
    
    unique  = set()
    
    for col in cols:
        unique = unique.union(set(df[col].values))
        
    return unique

def add_onclick(html):
    html= html.replace('<tr>','<tr onClick="h2h(this)">')    
    return html

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.urandom(12)
    app.run()