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

def calculate_idf_scores(documents):
    #instantiate CountVectorizer() 
    cv=CountVectorizer(
        stop_words=stopwords,
        dtype = np.float32,
        strip_accents = 'unicode',
        ngram_range=(1,1),
        min_df=2,
        #max_df=2.0
    ) 
    # this steps generates word counts for the words in your docs 
    print("count fit")
    word_count_vector=cv.fit_transform(documents)

    print("tfidf fit")
    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True) 
    tfidf_transformer.fit(word_count_vector)

    # print idf values 
    #df_idf = pd.DataFrame(tfidf_transformer.idf_, index=cv.get_feature_names(),columns=["idf_weights"]) 
    
    # sort ascending 
    #df_idf = df_idf.sort_values(by=['idf_weights'])
    #df_idf.to_csv("hallo1.csv")

    return tfidf_transformer, cv

def calculate_tf_idf_scores(documents,tfidf_transformer,cv):
    # count matrix 
    count_vector=cv.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector = tfidf_transformer.transform(count_vector)
    feature_names = cv.get_feature_names() 

    return feature_names, tf_idf_vector