import numpy as np
import pickle
import bpm.nyt_corpus as nyt
import pandas as pd
import os
import editdistance

from sklearn import preprocessing as skp
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 

# Save transformer and vectorizer globally for access
# (yeye, bad practice, i know)
tfidf_transformer = None
count_vectorizer = None

# Function that calculates the n most similar words in the vocabulary to a given term
# Currently not used in implementation
def get_closest_n(term,n):
    features = count_vectorizer.get_feature_names()
    feature_distances = np.full(len(features),0,dtype=np.int8)
    for i in range(0,len(features)):
        feature_distances[i] = editdistance.eval(term, features[i])
    idx = np.argpartition(feature_distances, n)
    return [features[i] for i in idx[:n]]

# Initialize the tf-idf value calculation by calculating all IDF values, 
# Or loading them from disk if that has already been done.
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

# dummy func to remove tokenization from CountVectorizer
def _dummy(x):
    return x

# Calculates the idf values of a given set of documents
def calculate_idf_scores(documents):
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

# A Custom implementation to calculate TF-IDF values without CountVectorizer
# Using Count vectorizer required having alld ata available at once for transform
# Here we use Counter, which can incrementally count objects.
def calculate_tf_idf_scores_counter(counters):
    vectors = []
    for c in counters:
        vectorizer_vocab = count_vectorizer.vocabulary_
        for n in list(c.keys()):
            if n not in vectorizer_vocab:
                del c[n]

        tfs = np.zeros(tfidf_transformer.idf_.size)
        for word in c.keys():
            tfs[vectorizer_vocab[word]] = c[word]
        tfidf = skp.normalize([np.multiply(tfs,tfidf_transformer.idf_)])[0]
        vectors.append(tfidf)

    return count_vectorizer.get_feature_names(), vectors