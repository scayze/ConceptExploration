import numpy as np
import pickle
import bpm.nyt_corpus as nyt
import pandas as pd
import os
import editdistance

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 

stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]

tfidf_transformer = None
count_vectorizer = None

def get_closest_n(term,n):
    features = count_vectorizer.get_feature_names()
    feature_distances = np.full(len(features),0,dtype=np.int8)
    for i in range(0,len(features)):
        feature_distances[i] = editdistance.eval(term, features[i])
    idx = np.argpartition(feature_distances, n)
    return [features[i] for i in idx[:n]]


    
def initialize_idf():
    global tfidf_transformer
    global count_vectorizer
    if os.path.isfile('idf_data.pck'):
        with open('idf_data.pck', 'rb') as f:
            data = pickle.load(f)
            tfidf_transformer = data[0]
            count_vectorizer = data[1]
    else:
        print("Generating IDF data from scratch")
        data = nyt.get_data_generator(pd.to_datetime("1970"),pd.to_datetime("2020"))
        #data = nyt.get_data_between(pd.to_datetime("1970"),pd.to_datetime("2020"))
        tfidf_transformer, count_vectorizer = calculate_idf_scores(data)
        with open('idf_data.pck', 'wb') as f:
            pickle.dump([tfidf_transformer,count_vectorizer], f)

def _dummy(x):
    return x

def calculate_idf_scores(documents,vocab=None):
    #instantiate CountVectorizer() 
    #No Ngram range as that is handled by textacy.extract over at processing.py
    cv=CountVectorizer(
        tokenizer = _dummy,
        preprocessor = _dummy,
        stop_words = None,
        dtype = np.int32,
        min_df=5,
    ) 
    # this steps generates word counts for the words in your docs 
    print("Count fit")
    word_count_vector=cv.fit_transform(documents)

    print("TF-IDF fit")
    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True) 
    tfidf_transformer.fit(word_count_vector)

    return tfidf_transformer, cv

def calculate_tf_idf_scores(documents):
    # count matrix 
    count_vector=count_vectorizer.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector = tfidf_transformer.transform(count_vector)
    feature_names = count_vectorizer.get_feature_names() 

    return feature_names, tf_idf_vector