import os
from typing import Counter

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
import itertools
import sklearn.metrics as skm

from flask import Flask, json, jsonify, g, redirect, request, url_for, render_template, send_from_directory

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

    query_id = "concordance" + str(term) + str(word) + str(date_from) + str(date_to)

    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)
    docs_per_month = nyt.get_raw_docs(date_from,date_to)

    for month_docs in docs_per_month:
        for doc in month_docs:

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
                print("found match")
            if len(output) > 15: break
        if len(output) > 15: break

    query_cache[query_id] = output
    with open('query_cache.pck', 'wb') as f:
        pickle.dump(query_cache, f)
    
    return jsonify(result=output)

#TODO: /_search_term, /_search_custom_glyph and get_tfidf_from_data have lots of duplicate code. Unify or split in functions

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
        if glyph_terms[i] not in tf_idf.count_vectorizer.vocabulary_: 
            raise InvalidTerms(glyph_terms[i])

    query_id = term + ",".join(glyph_terms) + str(date_from) + str(date_to)
    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    if term == "": return jsonify({})
    if glyph_terms == []: return jsonify({})

    app.logger.info('Request with' + 
        ' term:' + term +
        ' glyph_terms:' + ",".join(glyph_terms) +
        " from:" + date_from + 
        " to:" + date_to
    )

    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    c = Counter()
    df_list = nyt.get_data_generator_between(date_from,date_to)
    for df in df_list:
        df = df.loc[df["textdata"].apply(lambda x: term in x)]
        df["textdata"].apply(lambda x: c.update(x))

    print("calculate tfidf")
    names, vectors_list = tf_idf.calculate_tf_idf_scores_counter([c])
    matrix = vectors_list[0]

    for term in glyph_terms:
        idx = tf_idf.count_vectorizer.vocabulary_[term]
        word_data = {}
        word_data["position"] = list(we.get_embedding(term))
        word_data["tfidf"] = str(matrix[idx])
        output[term] = word_data

    #TODO: Show document counts in the starglpyh too??

    #Save to query_cache dict 
    query_cache[query_id] = output
    with open('query_cache.pck', 'wb') as f:
        pickle.dump(query_cache, f)

    #Send off response
    return jsonify(result=output)

@app.route('/_search_term')
def search_term():
    
    # Get all parameters from the request and convert them to the appropriate types
    term = request.args.get('term', 0, type=str)
    interval = request.args.get('interval', 0, type=int)
    date_from = request.args.get('from', 0, type=str)
    date_to = request.args.get('to', 0, type=str)
    count = int(request.args.get('count', 0, type=str))
    deep = bool(request.args.get('deep', 0, type=int)) #HACK: type=bool doesnt work, thus passing int with 0=False and 1=True

    # If the search term is not in our vocabulary, abort the request and send error back to client
    if term not in tf_idf.word2id: 
        raise InvalidTerms(term)

    # Generate the unique id for this query, and check if this has already been computed. If so, return it.
    query_id = str(term) + str(interval) + str(date_from) + str(date_to) + str(count) + str(deep)
    if query_id in query_cache:
        return jsonify(result=query_cache[query_id])

    # Also abort if the searchterm is an empty string
    if term =="": return jsonify({})

    # Log all relevant information to console
    app.logger.info('Request with' + 
        ' term:' + term +
        " interval:" + str(interval) + 
        " from:" + date_from + 
        " to:" + date_to + 
        " count:" + str(count) + 
        " deep:" + str(deep)
    )

    #Convert input strings to timestamps, and scrape timezone off
    date_from = pd.to_datetime(date_from).tz_localize(None)
    date_to = pd.to_datetime(date_to).tz_localize(None)

    # Generate a list of timestamps with the given interval and dates
    date_ranges = list(pd.date_range(date_from, date_to, freq= str(interval)+'MS')) 

    print("Counting")
    counters = []
    document_counts = []
    for i in range(0,len(date_ranges)-1):
        print(date_ranges[i])
        c = Counter()
        doc_count = 0
        df_list = nyt.get_data_generator_between(date_ranges[i],date_ranges[i+1])
        for df in df_list:
            df = df.loc[df["textdata"].apply(lambda x: term in x)]
            df["textdata"].apply(lambda x: c.update(x))
            doc_count += len(df.index)
        document_counts.append(doc_count)
        counters.append(c)

    print("calculate tfidf")
    names, vectors_list = tf_idf.calculate_tf_idf_scores_counter(counters)

    similarities = []
    for i in range(1,len(vectors_list)):
        # Calculate cosine similarity between tfidf vectors 
        # To Calculate a Semantic change value
        sim_array = skm.pairwise.cosine_similarity([vectors_list[i-1]],[vectors_list[i]])
        sim = sim_array[0,0]
        similarities.append(sim)
        print("Similarity: ", sim)
    
    print("calculate topn")
    output = {}
    for i in range(0,len(vectors_list)):
        matrix = vectors_list[i]

        # Calculate the top n relevant terms
        topn_idx = tools.get_topn_filtered(matrix,names,term,count)

        #Come up with a title for each column. (Here just Year + Month)
        t = pd.to_datetime(date_ranges[i]) 
        key = str(t.year) + "-" + str(t.month).rjust(2,"0")

        column_data = {}
        date_from = pd.to_datetime(date_ranges[i])
        date_to = pd.to_datetime(date_ranges[i+1])
        column_data["date_from"] = date_from
        column_data["date_to"] = date_to
        if i < len(similarities):
            column_data["similarity_to_next"] = similarities[i]

        word_list = {}
        for idx in topn_idx:
            w = names[idx]
            word_data = {}
            word_data["position"] = list(we.get_embedding(w))
            word_data["tfidf"] = str(matrix[idx])
            if deep: word_data["detail_data"] = get_tfidf_from_data(w,date_from,date_to)
            word_list[w] = word_data
        column_data["words"] = word_list
        doc_count = document_counts[i]
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

    print("Counting detail")
    c = Counter()
    doc_count = 0
    df_list = nyt.get_data_generator_between(date_from,date_to)
    for df in df_list:
        df = df.loc[df["textdata"].apply(lambda x: term in x)]
        df["textdata"].apply(lambda x: c.update(x))
        doc_count += len(df.index)

    print("calculate tfidf")
    names, vectors_list = tf_idf.calculate_tf_idf_scores_counter([c])
    
    matrix = vectors_list[0]
    topn_idx = tools.get_topn_filtered(matrix,names,term,5)

    word_list = {}
    for idx in topn_idx:
        w = names[idx]
        word_data = {}
        word_data["position"] = list(we.get_embedding(w))
        word_data["tfidf"] = str(matrix[idx])
        word_list[w] = word_data
    return word_list

#Start the Flask Server and load necessary files
if __name__ == "__main__":  
    
    if os.path.isfile('query_cache.pck'):
        with open('query_cache.pck', 'rb') as f:
            query_cache = pickle.load(f)
    else:
        query_cache = {}

    #Load IDF values from disk
    tf_idf.initialize_idf()
    we.initialize_embeddings()
    
    app.run(debug=False,host="0.0.0.0",port="8080")
    app.add_url_rule('/favicon.ico', redirect_to=url_for('static', filename='favicon.ico'))
