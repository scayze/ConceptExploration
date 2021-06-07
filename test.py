# %%
import spacy
from spacy.tokens import DocBin

import os
import pandas as pd
import bpm.nyt_corpus as nyt

import textacy
from textacy import extract 

import bpm.tf_idf as tf_idf

nlp = spacy.load("en_core_web_sm")
nlp.from_disk('project.nlp')

path = 'data/nyt_corpus/data/2000/01.spacy'

#%%
f = pd.to_datetime("2002-01-02")
t = pd.to_datetime("2003-02-01")
df = pd.read_pickle("hahahahahha.pck")

print(df.index)
#df.index = pd.to_datetime(df.index)
#df = df.sort_index()
df2 = df.loc[f:t]
f2 = pd.to_datetime("2002-01-02")
t2 = pd.to_datetime("2003-02-01")
df2 = df[["url"]]
df2.to_csv("ttestt.csv")


#%%
f2 = pd.to_datetime("2002-01-02")
t2 = pd.to_datetime("2003-02-01")

dates = ["2002-01-04","2002-01-14","2002-02-04","2002-02-04","2002-01-19"]
data = ["aa","aaa","ab","ac","ad"]
df3 = pd.DataFrame.from_dict({"date":dates, "data":data})
df3 = df3.set_index("date")
#df3 = df3.sort_index()
df3.index = pd.to_datetime(df3.index)
df4 = df3[f:t]

print(df2)
#%%

custom_stopwords = [x for x in open('data/stopwords/ranksnl_large.txt','r').read().split('\n')]
for w in custom_stopwords:
    nlp.vocab[w].is_stop = True
nlp.to_disk("project.nlp")

#%%
tf_idf.from_disk()
tf_idf.calculate_tf_idf_scores([["milk", "climate change"],[],["water","world","metal"]])

# %%


bin = DocBin(attrs=["LEMMA", "POS", "ENT_TYPE", "ENT_IOB"],store_user_data=True).from_disk(path)
docs = list(bin.get_docs(nlp.vocab))
en = textacy.load_spacy_lang("en_core_web_sm")

textlist = ["peter loves icecream, peter likes ducks","peter is going to the mall to eat icecream","the mall is big and peter loves it"]
docs = [textacy.make_spacy_doc(t, lang=en) for t in textlist]

for d in docs:
    print("_")
    for t in nyt.extract_terms(d):
        print(t.text)
#for f in test:
#    print(f)

#%%
result = tf_idf.get_tdidf(nlp,docs[1:4])

# %%
print(result[1])
print("HUH")
print(min(result[1]))
print(tex_idf.vectorizer.terms_list)

#%%
nlp = spacy.load("en_core_web_sm")
nlp.from_disk('project.nlp')
doc = nlp(
    "spaCy Doc or raw text in which to search for keyword. If a Doc, constituent text is grabbed via spacy.tokens.Doc.text. Note that spaCy annotations aren’t used at all here, they’re just a convenient owner of document text."
)
docs = list(nyt.get_raw_docs(pd.to_datetime("2000"),pd.to_datetime("2000-02")))
found = extract.kwic.keyword_in_context(
    docs[0],
    "war",
    ignore_case=True,
    window_width=100,

)
for f in found:
    print(f)
# %%
