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
