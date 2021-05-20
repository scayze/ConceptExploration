from datetime import date
import sys
sys.path.append("C:/Users/Manu/Documents/repos/D3Test/")

from pandas.io import pickle
import bpm.co_occurance as co
import bpm.nyt_corpus as nyt
import bpm.tools as tools
import pandas as pd
import pickle
import matplotlib.pyplot as plt
import numpy as np
import regex as re
import os

from flask import Flask, json, jsonify, g, redirect, request, url_for, render_template, send_from_directory

app = Flask(__name__)


all_data = None
tft = None
cv = None

glove_words = None
glove_data = None

def initialize_w2v():
    pass

def initialize_idf():
    print("load all data")
    all_data = nyt.get_data_between_pd("",pd.to_datetime("1970"),pd.to_datetime("2010"))
    print("get idf scores")
    a, b = co.calculate_idf_scores(all_data["data"])
    with open('idf_data.pk', 'wb') as f:
        pickle.dump([a,b], f)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/_get_concordance')
def find_matches():
    output = []
    term = request.args.get('term', 0, type=str)
    word = request.args.get('word', 0, type=str)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)

    app.logger.info('Request with' + 
        ' term:' + term +
        " word:" + word + 
        " from:" + date_from + 
        " to:" + date_to
    )


    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)
    df = nyt.get_data_between_pd(term,date_from,date_to)
    df = df[df["textdata"].str.contains(word)]
    
    for index, row in df.iterrows():
        url = row["url"]
        content = row["textdata"]
        occurances = [m.start() for m in re.finditer(word, content)]
        for o in occurances:
            left_from = max(0, o - 150)
            left_to = o
            right_from = o + len(word)
            right_to = o + min(len(content), len(word) + 150)
            
            occurance_dict = {}
            occurance_dict["left"] = content[left_from:left_to]
            occurance_dict["kwiq"] = word
            occurance_dict["right"] = content[right_from:right_to]
            occurance_dict["url"] = url
            output.append(occurance_dict)
    return jsonify(result=output)


@app.route('/_search_term')
def search_term():
    global all_data
    #Intialize tool when it hasnt been done yet
    #if type(all_data) == type(None):
    #    print("Loding data!")
    #    with open('pd_data.pck', 'rb') as f:
    #        pass
            #all_data = pickle.load(f)
            #print(all_data.head(10))

    output = {}
    
    term = request.args.get('term', 0, type=str)
    interval = request.args.get('interval', 0, type=int)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)
    count = int(request.args.get('count', 0, type=str))



    if term =="": return jsonify({})

    app.logger.info('Request with' + 
        ' term:' + term +
        " interval:" + str(interval) + 
        " from:" + date_from + 
        " to:" + date_to + 
        " count:" + str(count)
    )
    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    print("load data into memory")
    doc_list = nyt.get_data_between_pd(term,date_from,date_to)
    print("group")
    doc_list = tools.group_dataframe_pd(doc_list,interval,date_from,date_to)
    print("calculate statistics")
    #names, vectors = co.calculate_td_idf_scores2(doc_list["data"].to_list())
    #tft, cv = co.calculate_idf_scores(doc_list["data"].to_list())

    names, vectors = co.calculate_tf_idf_scores(doc_list["textdata"], tft, cv)
    
    print("calculate topn")
    for i in range(0,len(doc_list)):
        df = pd.DataFrame(vectors[i].T.todense(), index=names, columns=["tfidf"])
        topn = df.nlargest(count,"tfidf")
        t = pd.to_datetime(doc_list.index[i])
        key = str(t.year) + "-" + str(t.month).rjust(2,"0")

        column_data = {}
        date_from = pd.to_datetime(doc_list.index[i]).replace(day=1)
        column_data["date_from"] =  date_from
        column_data["date_to"] = date_from + pd.DateOffset(months=interval)

        word_list = {}
        for w in list(topn.index):
            word_data = {}
            word_data["position"] = [0,0]
            word_data["tfidf"] = str(topn.at[w,"tfidf"])
            if w in glove_words:
                idx = glove_words.index(w) 
                word_data["position"] = list(glove_data[idx])
            word_list[w] = word_data
        column_data["words"] = word_list
        output[key] = column_data

    return jsonify(result=output)

if __name__ == "__main__":
    #initialize_idf()
    #nyt.woops()
    #quit()
    with open('idf_data.pck', 'rb') as f:
        data = pickle.load(f)
        tft = data[0]
        cv = data[1]
        #print(data)
        # print idf values 
        #df_idf = pd.DataFrame(tft.idf_, index=cv.get_feature_names(),columns=["idf_weights"]) 
        #df_idf = df_idf.sort_values(by=['idf_weights'])
        #df_idf.to_csv("idf_values.csv")

    with open('2d_data.pck', 'rb') as f:
        data = pickle.load(f)
        glove_words = data[0]
        glove_data = data[1]
        #plt.scatter(glove_data[:, 0], glove_data[:, 1], s=1)
        #plt.show()
        #print(data)

    all_data = None
    
    app.run(debug=True)
    app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))