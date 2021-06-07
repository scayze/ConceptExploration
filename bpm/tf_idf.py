import numpy as np
import pickle
import dill

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 

stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]

tfidf_transformer = None
count_vectorizer = None

def from_disk():
    global tfidf_transformer
    global count_vectorizer
    with open('idf_data.pck', 'rb') as f:
        data = pickle.load(f)
        tfidf_transformer = data[0]
        count_vectorizer = data[1]

def _dummy(x):
    return x

def calculate_idf_scores(documents,vocab=None):
    #instantiate CountVectorizer() 
    #No Ngram range as that is handled by textacy.extract over at processing.py
    cv=CountVectorizer(
        tokenizer = _dummy,
        preprocessor = _dummy,
        stop_words = stopwords,
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

def calculate_tf_idf_scores(documents):
    # count matrix 
    count_vector=count_vectorizer.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector = tfidf_transformer.transform(count_vector)
    feature_names = count_vectorizer.get_feature_names() 

    return feature_names, tf_idf_vector