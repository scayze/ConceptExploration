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

class LemmaTokenizer(object):
    def __init__(self):
        self.wnl = WordNetLemmatizer()
    def __call__(self, articles):
        return [self.wnl.lemmatize(t) for t in word_tokenize(articles) if t not in stopwords]

def create_cooccurrence_matrix(sentences):
    cv = CountVectorizer(
        tokenizer=LemmaTokenizer(),
        ngram_range=(1,2),
        #stop_words = 'english',
        strip_accents = 'unicode',
        dtype = np.uint16,
        #min_df = 3
        #max_features=10000
    )
    # matrix of token counts
    X = cv.fit_transform(sentences)
    names = cv.get_feature_names() # This are the entity names (i.e. keywords)
    Xc = (X.T * X) # matrix manipulation
    Xc.setdiag(0) # set the diagonals to be zeroes as it's pointless to be 1
    #print(type(Xc))
    #print(Xc.data.nbytes)
    #return Xc, names
    #Xc.save_npz("lolo.npz")
    df = pd.DataFrame.sparse.from_spmatrix(Xc,columns = names, index = names)
    #df = pd.DataFrame(Xc.toarray(), columns = names, index = names)
    return df

def create_dataframe(interval,date_from,date_to):
    df = pd.read_csv("data/lemma1.csv")[["time","sentences"]]
    df["time"] = pd.to_datetime(df["time"],errors='coerce')
    df["sentences"] = df["sentences"].apply(lambda x: str(x))
    df = df.groupby(pd.Grouper(key="time",freq=str(interval) + "M"),as_index=True)
    df = df['sentences'].apply(lambda x: ''.join(x)).reset_index()
    if date_from != "" and date_to != "":
        df.index=pd.to_datetime(df.index)
        #df = df.between_time(date_from,date_to)
        df = df.loc[(df['time'] > pd.to_datetime(date_from)) & (df['time'] <= pd.to_datetime(date_to))]
    #print(df)
    #df.to_csv("scripts/data/testtest.csv")
    return df

def get_cooccurrence_matrix(df,term):
    matrices = {}
    for index, row in df.iterrows():
        sentences = []

        content = row["sentences"]
        if not isinstance(content, str): continue
        content_sentences = content.split(".")  
        
        for s in content_sentences:
            s = s.lower()
            if term in s or term == "" :
                s = re.sub(r'[^a-z\- ]+', '', s)
                sentences.append(s.lower())

        if len(sentences) == 0: continue

        matrices[str(row["time"])] = create_cooccurrence_matrix(sentences)

    return matrices

def save_cooccurrence_matrix(df):
    for index, row in df.iterrows():
        sentences = []

        content = row["sentences"]
        if not isinstance(content, str): continue
        content_sentences = content.split(".")  
        
        for s in content_sentences:
            s = s.lower()
            s = re.sub(r'[^a-z\- ]+', '', s)
            sentences.append(s.lower())

        if len(sentences) == 0: continue
        
        codf = create_cooccurrence_matrix(sentences)

        rowname = str(row["time"])
        filename = rowname[:len(rowname) - 9]
        codf.to_csv(r"scripts/data/co_m/" + filename + r".csv")

def collect_cooccurance_days(term):
    path = 'data/nyt_corpus/data/'
    i = 0

    df = pd.DataFrame([], columns=[])


    year_folders = [f.path for f in os.scandir(path) if f.is_dir()]

    for year_f in year_folders:
        month_folders = [f.path for f in os.scandir(year_f) if f.is_dir()]

        for month_f in month_folders:
            day_folders = [f.path for f in os.scandir(month_f) if f.is_dir()]

            for day_f in day_folders:
                names = []
                with open(day_f + "/test.pkl", "rb") as fp:   # Unpickling
                    names = pickle.load(fp)
                #Xc = scipy.sparse.load_npz(day_f + '/cooc.npz') remove scipy dependency
                #print(names)
                #day_df = pd.DataFrame.sparse.from_spmatrix(Xc,columns = names, index = names)
                #day_df = pd.read_pickle(day_f + "/cooc.gzip")
                

                #if term in day_df.columns: pass
                    #day_column = day_df[term]
                    #day_column = day_column.loc[(day_df!=0).any(1)]
                    #day_column.name = day_f
                    #df = df.merge(day_column, how="outer",left_index=True,right_index=True)
                #else:
                #    df[day_f] = 0
                #print(day_column.index)
                
                i+=1
                if i==10: break
                print(i)
            if i==10: break
        
        break
    df.fillna(0)
    df.to_csv("hahaha.csv")

def calculate_td_idf_scores(documents):
    tv = TfidfVectorizer (
        use_idf=True,
        #tokenizer=LemmaTokenizer(),
        ngram_range=(1,1),
        #stop_words = 'english',
        strip_accents = 'unicode',
        dtype = np.float32,
        max_features=1000000,
        min_df = 2,
        max_df = 0.8
    )
    document_vectors = tv.fit_transform(documents)
    names = tv.get_feature_names() # This are the entity names (i.e. keywords)
    #df = pd.DataFrame.sparse.from_spmatrix(document_vectors,columns = ["tfidf"]*len(documents), index = names)
    return names, document_vectors

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

def calculate_td_idf_scores2(documents):
    #instantiate CountVectorizer() 
    cv=CountVectorizer(
        stop_words= stopwords,
        dtype = np.float32,
        strip_accents = 'unicode',
        ngram_range=(1,2),
        min_df=2,
        max_df=2.0
    ) 
    # this steps generates word counts for the words in your docs 
    word_count_vector=cv.fit_transform(documents)

    tfidf_transformer=TfidfTransformer(smooth_idf=True,use_idf=True) 
    tfidf_transformer.fit(word_count_vector)

    # print idf values 
    df_idf = pd.DataFrame(tfidf_transformer.idf_, index=cv.get_feature_names(),columns=["idf_weights"]) 
    
    # sort ascending 
    df_idf = df_idf.sort_values(by=['idf_weights'])
    df_idf.to_csv("hallo1.csv")

    # count matrix 
    count_vector=cv.transform(documents) 
    
    # tf-idf scores 
    tf_idf_vector=tfidf_transformer.transform(count_vector)
    feature_names = cv.get_feature_names() 

    return feature_names, tf_idf_vector
