#%%
import itertools
from scipy.sparse import linalg
from spacy.tokens import DocBin

import os
import pandas as pd
import bpm.nyt_corpus as nyt

import textacy
from textacy import extract 

import bpm.tf_idf as tf_idf

#%%

import pickle
with open('idf_dataOLD.pck', 'rb') as f:
    data = pickle.load(f)
    tfidf_transformer = data[0]
    count_vectorizer = data[1]

word2id = count_vectorizer.vocabulary_
idf = tfidf_transformer.idf_
print(word2id)
print(idf)

with open('idf_data.pck', 'wb') as f:
    pickle.dump([word2id,idf], f)


#%%
import sklearn.metrics as skm
import numpy as np
a = np.array([[0.1,0.2,0.3,0.4,0.6,0.7]])
b = np.array([[0.1,0.2,0.56,0.7,0.6,0.7]])

c = np.ndarray([a,b])
print(c)

r = skm.pairwise.cosine_similarity(a,b)
print(r[0,0])

#%%
import bpm.nyt_corpus as nyt
import pandas as pd
start_date = pd.to_datetime("2000-01")
end_date = pd.to_datetime("2000-03")
docgen = nyt.get_doc_generator_between(start_date,end_date)
i = 0
for doc in docgen:
    i+=1
    print(doc[0:3])
print(i)
#%%
from datetime import date, timedelta

start_date = pd.to_datetime("2000-01")#.to_datetime64().astype("timedelta64[D]")
end_date = pd.to_datetime("2003")#.to_datetime64().astype("timedelta64[D]")
parts = list(pd.date_range(start_date, end_date, freq='12MS')) 

for i in parts: print(i)
#%%
delta = np.timedelta64(12,"M").astype("timedelta64[D]")
print(delta)
print(start_date)
while start_date <= end_date:
    #print(start_date.strftime("%Y-%m-%d"))
    start_date += delta
    print(start_date)

#%%
import os
import pickle
from collections import Counter
import itertools
import pandas as pd
import bpm.tf_idf as tf
import numpy as np

tf.initialize_idf()

#%%

example_data = [
    ["global warming","grizzly bear"],
    ["bush","peanuts"],
    ["global warming", "bush","climate change","peanuts"],
    ["banana","apple"]
]
import time
start = time.time()
a = tf.count_vectorizer.get_feature_names()
end = time.time()
print(end-start)
#%%
import editdistance
import numpy as np
def get_top_n(matrix,names,term,count):
    no_duplicates = False
    topn_idx = []
    duplicates = []

    while no_duplicates == False:
        no_duplicates = True
        new_count = count + len(duplicates)
        topn_idx = np.argpartition(matrix, -new_count)[-new_count:]

        for i in range(0,topn_idx.size):
            if names[topn_idx[i]] == term:
                if term not in duplicates: 
                    duplicates.append(term)
                    no_duplicates = False
                    break
            for j in range(i+1,topn_idx.size):
                nameI = names[topn_idx[i]]
                nameJ = names[topn_idx[j]]
                dist = editdistance.eval(nameI,nameJ)
                if dist < 5: 
                    longer = nameI if len(nameI) < len(nameJ) else nameJ
                    if longer not in duplicates: 
                        duplicates.append(longer)
                        no_duplicates = False
    output = []
    for i in topn_idx:
        if names[i] not in duplicates:
            output.append(i)
    return output
    


matrix = np.array([5,       16,     4,      32,      3,     1 ])
names =           ["aaaaa","bbbbb","ccccc","ddddd","eeeee","fffff"]


print("si",get_top_n(matrix,names,"aaaaa",5))

#%%
c = Counter()
for data in example_data:
    c.update(data)

# tf-idf scores 
n2, v2 = tf.calculate_tf_idf_scores_counter([c])
n1, v1 = tf.calculate_tf_idf_scores([itertools.chain.from_iterable(example_data)])


df = pd.DataFrame(v1[0].T.todense(), index=n1, columns=["tfidf"])
topn = df.nlargest(5,"tfidf")
print(topn)

df = pd.DataFrame(v2[0], index=n2, columns=["tfidf"])
topn = df.nlargest(5,"tfidf")
print(topn)

#%%^
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer 
import numpy as np

def _dummy(x):
    return x

cv=CountVectorizer(
    tokenizer = _dummy,
    preprocessor = _dummy,
    stop_words = None,
    dtype = np.int32,
    min_df=1,
)
type(cv.fit_transform([example_data[2]]))


#%%
import pandas as pd

def group_dataframe_pd(df):
    grouped_df = df.groupby(pd.Grouper(freq="12MS", label="left", origin=pd.to_datetime("2000-01-01")))
    df = grouped_df['url'].agg(textdata="count")
    return pd.DataFrame(df)

df = pd.read_csv("whattheactualfuck.csv")
df = df.set_index("date")
df.index = pd.to_datetime(df.index)

print(df["url"])
df = group_dataframe_pd(df)

print("GROUPED:")
print(df)




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
