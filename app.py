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

from flask import Flask, jsonify, g, redirect, request, url_for, render_template

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

@app.route('/_search_term')
def search_term():

    #Intialize tool when it hasnt been done yet
    if(all_data == None):
        pass#initialize_idf()

    output = {}
    term = request.args.get('term', 0, type=str)
    interval = request.args.get('interval', 0, type=int)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)
    count = int(request.args.get('count', 0, type=str))
    app.logger.info('Request with' + 
        ' term:' + term +
        " interval:" + str(interval) + 
        " from:" + date_from + 
        " to:" + date_to + 
        " count:" + str(count)
    )
    print("load data into memory")
    doc_list = nyt.get_data_between_pd(term,pd.to_datetime(date_from),pd.to_datetime(date_to))
    print("group")
    doc_list = tools.group_dataframe_pd(doc_list,interval)
    print("calculate statistics")
    #names, vectors = co.calculate_td_idf_scores2(doc_list["data"].to_list())
    #tft, cv = co.calculate_idf_scores(doc_list["data"].to_list())

    names, vectors = co.calculate_tf_idf_scores(doc_list["data"].to_list(), tft, cv)


    print("calculate topn")
    for i in range(0,len(doc_list)):
        df = pd.DataFrame(vectors[i].T.todense(), index=names, columns=["tfidf"])
        topn = df.nlargest(count,"tfidf")
        t = pd.to_datetime(doc_list.index[i])
        key = str(t.year) + "-" + str(t.month).rjust(2,"0")

        word_2d = {}
        for w in list(topn.index):
            word_2d[w] = [0,0]
            if w in glove_words:
                idx = glove_words.index(w)
                word_2d[w] = list(glove_data[idx])

        output[key] = word_2d
        #df = df.sort_values(by=["tfidf"],ascending=False)
        #print(topn)
    #matrices = co.get_cooccurrence_matrix(df,term)
    return jsonify(result=output)

if __name__ == "__main__":
    #initialize_idf()
    with open('idf_data.pk', 'rb') as f:
        data = pickle.load(f)
        tft = data[0]
        cv = data[1]
        #print(data)
        # print idf values 
        #df_idf = pd.DataFrame(tft.idf_, index=cv.get_feature_names(),columns=["idf_weights"]) 
        #df_idf = df_idf.sort_values(by=['idf_weights'])
        #df_idf.to_csv("idf_values.csv")

    with open('2d_data.pk', 'rb') as f:
        data = pickle.load(f)
        glove_words = data[0]
        glove_data = data[1]
        #plt.scatter(glove_data[:, 0], glove_data[:, 1], s=1)
        #plt.show()
        #print(data)
    
    app.run(debug=True)