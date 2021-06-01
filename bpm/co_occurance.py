import numpy as np
import pandas as pd
import os
import regex as re
#import scipy.sparse
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer 
from sklearn.feature_extraction.text import TfidfTransformer 
from sys import getsizeof
from nltk import word_tokenize
from nltk.corpus import stopwords
import pickle
from nltk.stem import WordNetLemmatizer 


#stopwords = stopwords.words('english')
stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]
def dummy(doc):
    return doc


def calculate_idf_scores(documents,vocab=None):
    #instantiate CountVectorizer() 
    #No Ngram range as that is handled by textacy.extract over at processing.py
    cv=CountVectorizer(
        tokenizer=dummy,
        preprocessor=dummy,
        stop_words=stopwords,
        dtype = np.int32,
        min_df=2,
    ) 
    # this steps generates word counts for the words in your docs 
    print("count fit")
    word_count_vector=cv.fit_transform(documents)

    print("tfidf fit")
    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True) 
    tfidf_transformer.fit(word_count_vector)

    return tfidf_transformer, cv

def calculate_tf_idf_scores(documents,tfidf_transformer,cv):
    # count matrix 
    count_vector=cv.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector = tfidf_transformer.transform(count_vector)
    feature_names = cv.get_feature_names() 

    return feature_names, tf_idf_vector