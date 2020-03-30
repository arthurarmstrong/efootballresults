import sqlite3,time
import pandas as pd
import numpy as np

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

    if not searchstr == 'None':
        searchfilter = " AND (HOME || AWAY) LIKE '%"+searchstr+"%'"
        labelsuffix = ' for search "'+searchstr+'".'
    else:
        searchfilter = ''
        labelsuffix = ''
        
    
    finalsheader= 'Finals Games'
    datefilter = "strftime('%s', DATE) > strftime('%s','now','-"+days+" days')"
    query = 'SELECT DATE, HOME, AWAY, "HOME SCORE", "AWAY SCORE", STAGE FROM MATCHES WHERE ('+datefilter + searchfilter + ') ORDER BY DATE DESC'    
    if comp == '1':
        dbpath = 'efootball.db'
        datefilter = "strftime('%s',DATE) BETWEEN strftime('%s','now','-"+days+" days') AND strftime('%s','now')"
    elif comp == '2':
        dbpath = 'esportsbattle.db'
        query = 'SELECT DATE, HOME, AWAY, "HOME SCORE", "AWAY SCORE", STAGE FROM MATCHES WHERE ('+datefilter + searchfilter + ') ORDER BY DATE DESC'
    elif comp =='3':
        dbpath = 'virtualbundesliga.db'
        finalsheader = 'Bundesliga Home Challenge'
        query = 'SELECT DATE, HOME || " (" || "HOME STATUS" || ")" AS HOME, AWAY || " (" || "AWAY STATUS" || ")" AS AWAY, "HOME SCORE", "AWAY SCORE", STAGE FROM MATCHES WHERE ('+datefilter + searchfilter + ' AND CONSOLE="PS4") ORDER BY DATE DESC'    
    else:
        return ''
    
    
    conn = sqlite3.connect(dbpath)
    c = conn.cursor()
    
    #Get the selected match data
    c.execute(query)   
    resp = c.fetchall()
    
    #Get the over under data
    c.execute('SELECT DATE, "HOME SCORE", "AWAY SCORE" FROM MATCHES WHERE ('+datefilter + searchfilter +'AND "HOME SCORE" + "AWAY SCORE" > 2'+ ')')
    totalresp = c.fetchall()
    #Get total stats
    gamecount = len(resp)
    overperc = len(totalresp)/gamecount
        
    responsetext = ''
    
    if resp:

        responsetext += '<div id="overunder" class="text-center"><table class="table table-bordered table-striped"><th colspan="2">Overall Stats'+labelsuffix+'</th><tr><td>Games</td><td>'+str(len(resp))+'</td></tr><tr><td>Over</td><td>'+str(len(totalresp))+' ('+str(round(overperc*100,1))+'%)</td></tr><tr><td>Under</td><td>'+str(len(resp)-len(totalresp))+' ('+str(round(100*(1-overperc),1))+'%)</td></tr></table></div><p>'
        
        #Turn the results into a pandas file
        table = pd.read_sql_query(query,conn)
        #Build a table of the group games
        #try:
        responsetext += '<div id="ladder" class="text-center center-block"><h2>Table - Group Games</h2><p>'
        grouptable = build_table(table[table['STAGE']=='Group Stage'])
        responsetext += grouptable.to_html() + '<p>'
        #except:
        #    pass
        try:
            #Make a new header for the finals table
            responsetext += f'<h2>Table - {finalsheader}</h2><p><div id="ladder" class="text-center center-block">'
            #Build a table of the finals games
            finaltable = build_table(table[table['STAGE']!='Group Stage'])
            responsetext += finaltable.to_html() + '</div><p>'
        except:
            pass
        
        #Build the table of individual games
        responsetext +='<table class="table table-dark table-bordered table-striped" id="gamestable"><tr><th onclick="sortTable(0)">Date</th><th onclick="sortTable(1)">Home</th><th onclick="sortTable(2)">Away</th><th onclick="sortTable(3)">Home Score</th><th onclick="sortTable(4)">Away Score</th></tr>'
        
        for r in resp:
            #Round scores
            if not r[3] == None:
                r = (r[0],r[1],r[2],int(r[3]),int(r[4]))
            else:
                r = (r[0],r[1],r[2],'-','-')
            #Add row
            responsetext += '<tr><td>'+str(r[0])+'</td><td>'+str(r[1])+'</td><td>'+str(r[2])+'</td><td>'+str(r[3])+'</td><td>'+str(r[4])+'</td></tr>'
    
    
        responsetext += '</table></div>'
    
    conn.close()    

    return responsetext


@app.route('/getdbupdatetime.php')
def getdbupdatetime():
    
    updatetime = os.path.getmtime('efootball.db') 
    return str(updatetime)

def build_table(df,season=None):

    #Build table of unique teams
    teams = get_unique_values_from_column(df,['HOME','AWAY'])
    #Remove duplicates
    df.drop_duplicates(subset=['DATE','HOME','AWAY'],inplace=True,keep='last')
    df.dropna(subset=['HOME SCORE','AWAY SCORE'],inplace=True)
    #Build zero vector to populate table with initially
    zero_column = np.zeros(len(teams),dtype=int)
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

def get_unique_values_from_column(df,cols):
    
    unique  = set()
    
    for col in cols:
        unique = unique.union(set(df[col].values))
        
    return unique

if __name__ == "__main__":
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SECRET_KEY'] = os.urandom(12)
    app.run()