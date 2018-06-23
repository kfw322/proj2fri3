import pandas as pd
import numpy as np
import os
import sqlalchemy
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Numeric, Text, Float
from sqlalchemy.sql import text
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base
import matplotlib.pyplot as plt
from flask import Flask, jsonify, render_template, request, redirect
import json
from datetime import datetime
from dateutil.parser import parse

engine = create_engine("sqlite:///data.sqlite")
conn = engine.connect()
Base= automap_base()
Base.prepare(engine,reflect=True)
Base.classes.keys()
inspector=inspect(engine)
inspector.get_table_names()
inspector.get_columns("DPI")
inspector.get_columns("FPSR")
inspector.get_columns("PCE")
inspector.get_columns("acs2015_county_data")

class DPI(Base):
    __tablename__ = "DPI"
    __table_args__ = {"extend_existing":True}
    field1 = Column(Text,primary_key=True)

class FPSR(Base):
    __tablename__ = "FPSR"
    __table_args__ = {"extend_existing":True}
    DATE = Column(Text,primary_key=True)

class PCE(Base):
    __tablename__ = "PCE"
    __table_args__ = {"extend_existing":True}
    GeoFIPS = Column(Integer,primary_key=True)
    Line = Column(Text,primary_key=True)

class DEMO(Base):
    __tablename__ = "acs2015_county_data"
    __table_args__ = {"extend_existing":True}
    CensusId = Column(Integer,primary_key=True)

Base.prepare()
session=Session(engine)
app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/visualization_1")
def viz_1():
    return render_template("visualization_1.html")

@app.route("/visualization_2")
def viz_2():
    return render_template("visualization_2.html")

@app.route("/visualization_3")
def viz_3():
    return render_template("visualization_3.html")

@app.route("/statelist")
def statelist():
    listofstates=[]
    for row in session.query(PCE):
        if int(row.GeoFIPS) < 60000: 
            listofstates.append(row.GeoName)
    statelist = []
    statelist = sorted(list(set(listofstates)))    
    return(jsonify(statelist))

@app.route("/savings")
def savings():
    savings_data_dict = {}
    for row in session.query(FPSR):
        savings_data_dict[str(parse(row.DATE).strftime("%Y-%m-%d"))] = row.USPersonalSavingsRate
    return(jsonify(savings_data_dict))

@app.route("/pce/<state>")
def pce(state):
    datadict = {}
    for year in range (1997,2017,1):
        y=str(year)
        datadict[y] = {}
        sqlquery = str(r' select "' + y + r'" from PCE WHERE GeoName= "' + state + r'" AND Line = "1"')
        for row in conn.engine.execute(sqlquery):
            datadict[y]["Total PCE"] = str(row[0])
        sqlquery = str(r' select "' + y + r'" from PCE WHERE GeoName= "' + state + r'" AND Line = "2"')
        for row in conn.engine.execute(sqlquery):
            datadict[y]["Goods"] = str(row[0])
        sqlquery = str(r' select "' + y + r'" from PCE WHERE GeoName= "' + state + r'" AND Line = "13"')
        for row in conn.engine.execute(sqlquery):
            datadict[y]["Services"] = str(row[0])
    return(jsonify(datadict))

@app.route("/pcedetail/<state>")
def pced(state):
    pcedetail = {}
    for year in range (1997,2017,1):
        y=str(year)
        pcedetail[y] = {}
        sqlquery = str(r' select "Line", "Description", "' + y + r'" from PCE WHERE GeoName= "' + state + r'"')
        for row in conn.engine.execute(sqlquery):
            pcedetail[y][str(row.Description + " (" + row.Line + ")")] = row[2]
    return(jsonify(pcedetail))

@app.route("/pcegraph/<state>")
def pceg(state):

    rawpopdata = pd.read_csv("https://raw.githubusercontent.com/aaronpenne/data_visualization/master/population/data/USA_Population_of_States_US_Census_Intercensal_Tables_1917-2017.csv")
    rawpopdf = rawpopdata.rename(columns={'': '','Year': 'Year','AK': 'Alaska','AL': 'Alabama','AR': 'Arkansas','AZ': 'Arizona','CA': 'California','CO': 'Colorado','CT': 'Connecticut','DC': 'District of Columbia','DE': 'Delaware','FL': 'Florida','GA': 'Georgia','HI': 'Hawaii','IA': 'Iowa','ID': 'Idaho','IL': 'Illinois','IN': 'Indiana','KS': 'Kansas','KY': 'Kentucky','LA': 'Louisiana','MA': 'Massachusetts','MD': 'Maryland','ME': 'Maine','MI': 'Michigan','MN': 'Minnesota','MO': 'Missouri','MS': 'Mississippi','MT': 'Montana','NC': 'North Carolina','ND': 'North Dakota','NE': 'Nebraska','NH': 'New Hampshire','NJ': 'New Jersey','NM': 'New Mexico','NV': 'Nevada','NY': 'New York','OH': 'Ohio','OK': 'Oklahoma','OR': 'Oregon','PA': 'Pennsylvania','RI': 'Rhode Island','SC': 'South Carolina','SD': 'South Dakota','TN': 'Tennessee','TX': 'Texas','UT': 'Utah','VA': 'Virginia','VT': 'Vermont','WA': 'Washington','WI': 'Wisconsin','WV': 'West Virginia','WY': 'Wyoming','US':'United States'})
    lessrawpopdf = rawpopdf[(rawpopdf.Year >= 1997) & (rawpopdf.Year <= 2016)]
    lessrawpopdf = lessrawpopdf.set_index("Year").T.reset_index()
    lessrawpopdf.columns.values[0] = "State"
    statepopres = lessrawpopdf[(lessrawpopdf.State==state)].set_index("State")
    sp = statepopres.T.reset_index()
    sp.columns=["Year","Pop"]
    sp_y = sp["Year"].apply(str)
    sp_p = sp["Pop"]
    population_dict = dict(zip(sp_y,sp_p))
    dpidict = {}
    unemployment_dict = { "1997" : .953,"1998" : .956,"1999" : .960,"2000" : .961,"2001" : .943,"2002" : .940,"2003" : .953,"2004" : .946,"2005" : .951,"2006" : .956,"2007" : .950,"2008" : .927,"2009" : .901,"2010" : .907,"2011" : .915,"2012" : .921,"2013" : .933,"2014" : .944,"2015" : .950,"2016" : .953 }
    for row in conn.engine.execute(r'select TimePeriod, DataValue from DPI where GeoName like "' + state + r'%"'):
        if 1996 < int(row.TimePeriod) < 2017:
            for rrr in conn.engine.execute(r'select "' + str(row.TimePeriod) + r'" from PCE where GeoName= "' + state + r'" and Line = "1"'):
                dpidict[row.TimePeriod] = (((float(row.DataValue) / 1000000) * float(unemployment_dict[str(row.TimePeriod)] * population_dict[row.TimePeriod])) - float(rrr[0]))
    label = []
    alldata = []
    dpidata = []
    years = []
    backgroundColor = ["rgba(0,127,0, 0.8)","rgba(114,147,203, 0.8)","rgba(225,151,76, 0.8)","rgba(132,186,91, 0.8)","rgba(211,94,96, 0.8)",
    "rgba(128,133,133, 0.8)","rgba(144,103,167, 0.8)","rgba(171,104,87, 0.8)","rgba(204,194,16, 0.8)",
    "rgba(114,147,203, 0.8)","rgba(225,151,76, 0.8)","rgba(132,186,91, 0.8)","rgba(211,94,96, 0.8)",
    "rgba(128,133,133, 0.8)","rgba(144,103,167, 0.8)","rgba(171,104,87, 0.8)","rgba(204,194,16, 0.8)"]
    years.extend(range(1997,2017))
    labels = [str(x) for x in years]
    for line in [4,5,6,7,9,10,11,12,15,16,17,18,19,20,21,22]:
        partdata = []
        for row in conn.engine.execute(str(r'select "Description" from PCE WHERE GeoName= "' + state + r'" AND Line = "' + str(line) + r'"')):
            label.append(str(row[0]))
        dpidata = []
        for year in range (1997,2017,1):
            dpidata.append(int(dpidict[str(year)]))
            sqlquery = str(r'select "' + str(year) + r'" from PCE WHERE GeoName= "' + state + r'" AND Line = "' + str(line) + r'"')
            for row in conn.engine.execute(sqlquery):
                partdata.append(int(row[0]))
        alldata.append(partdata)     
    alldata.insert(0,dpidata)
    label.insert(0,(str("SAVINGS PERCENTAGE")))
    datadct = {}
    datadct["labels"] = labels
    datadct["datasets"] = []
    
    for x in range(len(alldata)):
        datadct["datasets"].append({"label":str(label[x]),"data":alldata[x],"backgroundColor":backgroundColor[x],"hoverBorderColor":"gray","hoverBorderWidth":4})
    return render_template("graph.html",datadct=datadct,state=state)

@app.route("/countydata")
def county():
    slist = {}
    
    for rs in conn.engine.execute(r'select distinct "State" from acs2015_county_data'):
        s=str(rs[0])
        slist[s] = {}
        for rc in conn.engine.execute(r'select distinct "County" from acs2015_county_data where State="' + s + r'"'):
            c=str(rc[0])
            slist[s][c] = pd.read_sql_query(r'select * from acs2015_county_data where State="' + s + r'" and County="' + c + r'"',engine).T.to_dict()
    
    return(jsonify(slist))

@app.route("/income/<state>/<year>")
def incy(state,year):
    for row in conn.engine.execute(r'select DataValue from DPI where GeoName like "' + state + r'%" and TimePeriod="' + year + r'"'):
        inc = str(row[0])
    return(inc)

@app.route("/income/<state>/all")
def inc(state):
    incdict = {}    
    for row in conn.engine.execute(r'select TimePeriod, DataValue from DPI where GeoName like "' + state + r'%"'):
        if 1997 <= int(row.TimePeriod) <= 2016:
            incdict[row.TimePeriod] = row.DataValue
    return(jsonify(incdict))
        







if __name__ == "__main__":
    app.run(debug=True)