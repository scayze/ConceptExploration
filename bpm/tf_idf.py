#
# This file does all work related to processing the TFIDF scores of the data
#

import numpy as np
import pickle
import bpm.nyt_corpus as nyt
import pandas as pd
import os

from sklearn import preprocessing as skp
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 

#TODO: Make this file a class.
# Save the two dictionaries for converting between IDs and terms, and the idf values, globally for access
word2id = None
id2word = None
idf = None

# Initialize the tf-idf value calculation by calculating all IDF values, 
# Or loading them from disk if that has already been done.
def initialize_idf():
    global word2id
    global id2word
    global idf
    
    if os.path.isfile('idf_data.pck'):
        with open('idf_data.pck', 'rb') as f:
            print("loading idf")
            data = pickle.load(f)
            print("loaded idf")
            word2id = data[0]
            idf = data[1]
    else:
        print("Generating IDF data from scratch")
        data = nyt.get_doc_generator_between(pd.to_datetime("1970"),pd.to_datetime("2020"))
        count_vectorizer, tfidf_transformer = calculate_idf_scores(data)
        with open('idf_data.pck', 'wb') as f:
            word2id = count_vectorizer.vocabulary_
            idf = tfidf_transformer.idf_
            pickle.dump([word2id,idf], f)
    id2word = {v: k for k, v in word2id.items()}  

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

    return cv, tfidf_transformer

# A Custom implementation to calculate TF-IDF values without CountVectorizer
# Using Count vectorizer required having alld ata available at once for transform
# Here we use Counter, which can incrementally count objects.
def calculate_tf_idf_scores(tf_lists):
    vectors = []
    for tfs in tf_lists:
        tfidf = skp.normalize(tfs.multiply(idf))[0]
        vectors.append(tfidf)

    return id2word, vectors

# DEPRECEATED: calculate_tf_idf_scores is a much faster replacement.
# A Custom implementation to calculate TF-IDF values without CountVectorizer
# Using Count vectorizer required having all data available at once for transform
# Here we use Counter, which can incrementally count objects.
def calculate_tf_idf_scores_counter(counters):
    vectors = []
    for c in counters:
        vectorizer_vocab = word2id
        for n in list(c.keys()):
            if n not in vectorizer_vocab:
                del c[n]

        tfs = np.zeros(idf.size)
        for word in c.keys():
            tfs[vectorizer_vocab[word]] = c[word]
        tfidf = skp.normalize([np.multiply(tfs,idf)])[0]
        vectors.append(tfidf)

    return id2word, vectors