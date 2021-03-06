import os
from typing import Counter

from scipy.sparse.csr import csr_matrix
import scipy
from sklearn import utils

import bpm.tf_idf as tf_idf
import bpm.nyt_corpus as nyt
import bpm.tools as tools
import bpm.word_embeddings as we
import numpy as np

import pandas as pd
from pandas.io import pickle

from textacy import extract

import pickle
import re
import copy
import json
import itertools
import sklearn.metrics as skm

from flask import Flask, json, jsonify, g, redirect, request, url_for, render_template, send_from_directory
from werkzeug.middleware.profiler import ProfilerMiddleware

app = Flask(__name__)

query_cache = {}

class InvalidTerms(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        super().__init__()
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@app.errorhandler(InvalidTerms)
def invalid_api_usage(e):
    return jsonify(e.to_dict())

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/_get_concordance')
def find_matches():
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

    query_id = "concordance" + str(term) + str(word) + str(date_from) + str(date_to)

    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)
    output = nyt.keyword_in_context(date_from,date_to,term,word,10)

    query_cache[query_id] = output
    save_cache()
    
    return jsonify(result=output)

#When multiple queries are running simultaniously, multiple threads are trying to open the file with writing permission. 
#This causes crash, we just skip writing the cache in those cases. No data will be lost, and it will just be written next time the cache is saved.
def save_cache():
    try:
        with open('query_cache.pck', 'wb') as f:
            pickle.dump(query_cache, f)
    except RuntimeError:
        print("RuntimerError, skipping cache save")


# This function is called when the user changed the terms in the input field of the detail view. It recalculates the scores of that term.
@app.route('/_search_custom_glyph')
def search_custom_glyph():
    output = {}
    
    term = request.args.get('term', 0, type=str)
    glyph_terms = request.args.get('glyph_terms', 0, type=str)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)

    #Split on commas, remove leading and trailing whitepsace from each term, and remove duplicate whitespace
    glyph_terms = glyph_terms.lower().split(",")
    for i in range(0,len(glyph_terms)):
        glyph_terms[i] = glyph_terms[i].strip()
        glyph_terms[i] = re.sub(' +', ' ', glyph_terms[i])
        if glyph_terms[i] not in tf_idf.word2id: 
            raise InvalidTerms(glyph_terms[i])

    query_id = term + ",".join(glyph_terms) + str(date_from) + str(date_to)
    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    if term == "": return jsonify({})
    if glyph_terms == []: return jsonify({})

    app.logger.info('Request with' + 
        ' \nterm:' + term +
        ' \nglyph_terms:' + ",".join(glyph_terms) +
        " \nfrom:" + date_from + 
        " \nto:" + date_to
    )

    matrix = tfidfdata(term,date_from,date_to,1,True)["tfidf_data"]

    for term in glyph_terms:
        idx = tf_idf.word2id[term]

        word_data = {}
        word_data["position"] = list(we.get_embedding(term))
        word_data["tfidf"] = str(matrix[0,idx])
        output[term] = word_data

    #TODO: Show document counts in the starglpyh too??

    #Save to query_cache dict 
    query_cache[query_id] = copy.deepcopy(output)
    save_cache()

    #Send off response 
    return jsonify(result=output)

@app.route('/_search_similar')
def search_similar():
    # Get all parameters from the request and convert them to the appropriate types
    term = request.args.get('term', 0, type=str).lower()

    output = we.find_similar(term)
    return jsonify(result=output)

@app.route('/_search_detail')
def search_detail():
    # Get all parameters from the request and convert them to the appropriate types
    term = request.args.get('term', 0, type=str).lower()

    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)

    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    output = tfidfdata(term,date_from,date_to,5)
    return jsonify(result=output)

#This function is called when the user submits a query. NEWNENWENWNENWNEWNEW
@app.route('/_search_term')
def search_term():
    
    # Get all parameters from the request and convert them to the appropriate types
    term = request.args.get('term', 0, type=str).lower()
    interval = request.args.get('interval', 0, type=int)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)
    result_count = int(request.args.get('count', 0, type=str))
    deep = bool(request.args.get('deep', 0, type=int)) #HACK: type=bool doesnt work, thus passing int with 0=False and 1=True

    # If the search term is not in our vocabulary, abort the request and send error back to client
    if term not in tf_idf.word2id: 
        raise InvalidTerms(term)

    # Also abort if the search term is an empty string
    if term =="": return jsonify({})
    term_id = tf_idf.word2id[term]

    # Log all relevant information to console
    app.logger.info('Request with' + 
        ' term:' + term +
        " interval:" + str(interval) + 
        " from:" + date_from + 
        " to:" + date_to + 
        " count:" + str(result_count) + 
        " deep:" + str(deep)
    )

    #Convert input strings to timestamps, and scrape timezone off
    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    # Generate a list of timestamps with the given interval and dates
    date_ranges = list(pd.date_range(date_from, date_to, freq= str(interval)+'MS')) 

    # load all data, filter it by relevant articles, and count the appearing features together.
    output = []
    for i in range(0,len(date_ranges)-1):

        #Calculate its data
        #Add 5 "backup terms" on top of result count, incase the user wants to delete entries
        column = tfidfdata(term,date_ranges[i],date_ranges[i+1],result_count + 5, True)
        if deep: 
            for word in column["words"]:
                detail_data = tfidfdata(word,date_ranges[i],date_ranges[i+1],5)
                column["words"][word]["detail_data"] = detail_data         
            
        output.append(column)
    
    for i in range(1,len(output)):
        column = output[i]
        last_column = output[i-1]
        sim_array = skm.pairwise.cosine_similarity(last_column["tfidf_data"],column["tfidf_data"])
        last_column["similarity_to_next"] = sim_array[0,0]
        
    tools.scrub(output,"tfidf_data")

    #Send off response
    return jsonify(result=output)

def tfidfdata(term,date_from,date_to,result_count, base = False):
    # If the search term is not in our vocabulary, abort the request and send error back to client
    if term not in tf_idf.word2id: 
        raise InvalidTerms(term)

    # Generate the unique id for this query, and check if this has already been computed. If so, return it.
    query_id = str(term) + str(date_from) + str(date_to)
    if (query_id in query_cache) and (base == False): 
        print("cache hit")
        if len(query_cache[query_id]["words"]) < result_count: 
            print("cache not deep enough")
        else:
            return copy.deepcopy(query_cache[query_id])

    # Also abort if the search term is an empty string
    if term =="": return jsonify({})
    term_id = tf_idf.word2id[term]

    #Convert input strings to timestamps, and scrape timezone off
    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    # load all data, filter it by relevant articles, and count the appearing features together.
    print("Adding Counts")
    doc_count = 0

    count = csr_matrix((1,len(tf_idf.idf)),dtype=np.int32)
    df_list = nyt.get_data_generator_between(date_from,date_to)

    for df in df_list:
        #Filter the data by if it includes the desired searchterm
        df = df.loc[df["textdata"].apply(lambda x: term_id in x.indices)]
        #Abort if the data does not contain the searchterm at all
        if len(df.index) == 0: continue
        #Add the counts 
        sparse_stack = scipy.sparse.vstack(df["textdata"])
        sparse_sum = sparse_stack.sum(axis=0)
        count += csr_matrix(sparse_sum)
        doc_count += len(df.index)

    print("Calculate TFIDF")
    names, vectors_list = tf_idf.calculate_tf_idf_scores([count])
    
    # Calculate the top n relevant terms
    matrix = vectors_list[0]
    topn_idx = tools.get_topn_filtered(matrix,names,term,result_count)

    #Come up with a title for each column. (Here just Year + Month)
    output = {}
    output["date_from"] = date_from
    output["date_to"] = date_to
    output["document_count"] = doc_count
    output["position"] = list(we.get_embedding(term))

    word_list = {}
    for idx in topn_idx:
        w = names[idx]
        word_data = {}
        word_data["position"] = list(we.get_embedding(w))
        word_data["tfidf"] = str(matrix[0,idx])
        word_list[w] = word_data

    output["words"] = word_list

    #Save to query_cache dict 
    query_cache[query_id] = copy.deepcopy(output)
    save_cache()

    #If its the base query, additionally save the matrix for similarity calculations. This should not be included in the cache
    if base:
        output["tfidf_data"] = matrix

    #Send off response
    return output

#Load the query cache from disk. If it does not exist, create an empty one.
if os.path.isfile('query_cache.pck'):
    with open('query_cache.pck', 'rb') as f:
        query_cache = pickle.load(f)
else:
    query_cache = {}

#Load IDF values from disk
tf_idf.initialize_idf()
we.initialize_embeddings()

#Start the Flask Server and load necessary files
if __name__ == "__main__":  
    #print("hlo")
    #app.config['PROFILE'] = True
    #app.wsgi_app = ProfilerMiddleware(app.wsgi_app)
    app.run(debug=True,host="0.0.0.0",port="8080")
    app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))
