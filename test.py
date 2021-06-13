#%%
from spacy.tokens import DocBin

import os
import pandas as pd
import bpm.nyt_corpus as nyt

import textacy
from textacy import extract 

import bpm.tf_idf as tf_idf


path = 'data/nyt_corpus/data/2000/01.spacy'
#%%
import editdistance
print(editdistance.eval('dr. robinson', 'robinson'))

print(editdistance.eval('carbon cycle', 'carbon sinks'))

#%%
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 
import numpy as np

def _dummy(x):
    return x

def calculate_idf_scores(documents,vocab=None):
    #instantiate CountVectorizer() 
    #No Ngram range as that is handled by textacy.extract over at processing.py
    stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]
    cv=CountVectorizer(
        tokenizer = _dummy,
        preprocessor = _dummy,
        stop_words = stopwords,
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

def calculate_tf_idf_scores(documents,count_vectorizer,tfidf_transformer):
    # count matrix 
    count_vector=count_vectorizer.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector = tfidf_transformer.transform(count_vector)
    feature_names = count_vectorizer.get_feature_names() 

    return feature_names, tf_idf_vector

#%%
example_data = [
    ["said","ivey"],
    ["ivey","peanuts"],
    ["a.m. appointment","appointment","peanuts"],
    ["banana","apple"]
]

tft, cv = calculate_idf_scores(example_data)
print(cv.get_feature_names())

calculate_tf_idf_scores(example_data[0:1],cv,tft)

#%% Add Stopwords to spacy pipe
import spacy
nlp = spacy.load("en_core_web_sm")
nlp.from_disk('nlpnlpnlp')

custom_stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]
print(custom_stopwords)

for w in custom_stopwords:
    #nlp.vocab[w].is_stop = True
    lex = nlp.vocab[w]
    lex.is_stop = True
nlp.to_disk("nlpnlpnlp")


# %% Generate term dfs
import bpm.nyt_corpus as nyt
import pandas as pd
nyt.generate_term_dfs(date_from=pd.to_datetime("2002"))
# %% HACK: Remove stopwords from term dfs
import pandas as pd
stopwords = set([x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')])

def clean_terms(df):
    df["textdata"] = df["textdata"].apply(lambda x:
        [y for y in x
        if not any(word in stopwords for word in y.split(" "))]
    )
    return df



example_data = [["ivey said","ivey"],["ivey","peanuts"],["a.m. appointment","appointment"],["banana","apple"]]
df = pd.DataFrame.from_dict({"textdata":example_data})
print(df)
df2 = clean_terms(df)


# %%
import pandas as pd
path = 'data/nyt_corpus/data/'
for root, dirs, files in os.walk(path):
    for f in files:
        if not f.endswith('.pck'): continue
        p = os.path.join(root, f) #Get full path between the base path and the file
        df = pd.read_pickle(p)
        df = clean_terms(df)
        print(p)
        df.to_pickle(p)

# %%
