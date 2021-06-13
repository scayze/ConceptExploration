import os

import bpm.tf_idf as tf_idf
import bpm.nyt_corpus as nyt
import bpm.tools as tools
import bpm.word_embeddings as we

import pandas as pd
from pandas.io import pickle

from textacy import extract

import pickle
import itertools

from flask import Flask, json, jsonify, g, redirect, request, url_for, render_template, send_from_directory

app = Flask(__name__)

query_cache = {}

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
    docs = nyt.get_raw_docs(date_from,date_to)

    for doc in docs:

        #Check for single match in a kinda weird way
        matches = extract.matches.regex_matches(doc,term)

        found = False
        for m in matches:
            found = True
            break
        if not found: continue

        #Find KWIQ matches
        matches = extract.kwic.keyword_in_context(doc,word,ignore_case=True,window_width=100)
        for m in matches:
            occurance_dict = {}
            occurance_dict["left"] = m[0]
            occurance_dict["kwiq"] = m[1]
            occurance_dict["right"] = m[2] 
            occurance_dict["url"] = doc.user_data["url"]
            output.append(occurance_dict)
    return jsonify(result=output)


@app.route('/_search_term')
def search_term():
    output = {}
    
    term = request.args.get('term', 0, type=str)
    interval = request.args.get('interval', 0, type=int)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)
    count = int(request.args.get('count', 0, type=str))
    deep = bool(request.args.get('deep', 0, type=int)) #HACK: type=bool doesnt work, thus passing int with 0=False and 1=True

    query_id = str(term) + str(interval) + str(date_from) + str(date_to) + str(count) + str(deep)

    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    if term =="": return jsonify({})

    app.logger.info('Request with' + 
        ' term:' + term +
        " interval:" + str(interval) + 
        " from:" + date_from + 
        " to:" + date_to + 
        " count:" + str(count) + 
        " deep:" + str(deep)
    )
    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    doc_list = None
    if nyt.last_query_df is not None and (date_from >= nyt.last_query_from) and (date_to <= nyt.last_query_to):
        print("Using data of previous query")
        doc_list = nyt.last_query_df
        doc_list = doc_list.sort_index() #Not sure why it needs to be sorted *again* but here we are
        doc_list = doc_list.loc[date_from:date_to]
    else:
        print("loading data anew")
        doc_list = nyt.get_data_between(date_from,date_to)
    print("filter data by term")
    doc_list = doc_list.loc[doc_list["textdata"].apply(lambda x: term in x)]
    print("group data by date")
    doc_list = tools.group_dataframe_pd(doc_list,interval,date_from) 
    print(doc_list)
    print("calculate statistics")

    names, vectors = tf_idf.calculate_tf_idf_scores(doc_list["textdata"])
    
    print("calculate topn")
    for i in range(0,len(doc_list)):
        matrix = vectors[i]
        #df = pd.DataFrame(vectors[i].T.todense(), index=names, columns=["tfidf"])
        #topn = df.nlargest(count,"tfidf")
        topn_idx = tools.top_n_idx_sparse(matrix,count)[0]
        t = pd.to_datetime(doc_list.index[i]) 
        key = str(t.year) + "-" + str(t.month).rjust(2,"0")

        column_data = {}
        date_from = pd.to_datetime(doc_list.index[i])
        date_to = date_from + pd.DateOffset(months=interval)
        column_data["date_from"] = date_from
        column_data["date_to"] = date_to

        #print(names)
        print(type(names))

        word_list = {}
        for idx in topn_idx:
            w = names[idx]
            word_data = {}
            word_data["position"] = list(we.get_embedding(w))
            word_data["tfidf"] = str(matrix[0,idx])
            if deep: word_data["detail_data"] = get_tfidf_from_data(w,date_from,date_to)
            word_list[w] = word_data
        column_data["words"] = word_list
        doc_count = int(doc_list.iloc[i]["document_count"])
        print(doc_count)
        column_data["document_count"] = doc_count
        output[key] = column_data

    #Save to query_cache dict 
    query_cache[query_id] = output
    with open('query_cache.pck', 'wb') as f:
        pickle.dump(query_cache, f)

    #Send off response
    return jsonify(result=output)

def get_tfidf_from_data(term,date_from,date_to):
    doc_list = None
    if nyt.last_query_df is not None and (date_from >= nyt.last_query_from) and (date_to <= nyt.last_query_to):
        #print("Using data of previous query")
        date_from = pd.to_datetime(date_from)
        date_to = pd.to_datetime(date_to)

        doc_list = nyt.last_query_df
        doc_list = doc_list.sort_index()
        doc_list = doc_list.loc[date_from:date_to]
    else:
        print("existing data wasnt loaded")
        print(date_from)
        print(date_to)
        print(nyt.last_query_from)
        print(nyt.last_query_to)
    
    doc_list = doc_list.loc[doc_list["textdata"].apply(lambda x: term in x)]
    single_list = itertools.chain.from_iterable(doc_list["textdata"])
    names, vectors = tf_idf.calculate_tf_idf_scores([single_list])

    matrix = vectors[0]
    topn_idx = tools.top_n_idx_sparse(matrix,5)[0]

    word_list = {}
    for idx in topn_idx:
        w = names[idx]
        word_data = {}
        word_data["position"] = list(we.get_embedding(w))
        word_data["tfidf"] = str(matrix[0,idx])
        word_list[w] = word_data
    return word_list

if __name__ == "__main__":  
    if os.path.isfile('query_cache.pck'):
        with open('query_cache.pck', 'rb') as f:
            query_cache = pickle.load(f)
    else:
        query_cache = {}

    #Load IDF values from disk
    tf_idf.initialize_idf()
    we.initialize_embeddings()
    
    app.run(debug=True)
    app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))