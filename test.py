# %%
import spacy
from spacy.tokens import DocBin

import os
import pandas as pd
import bpm.nyt_corpus as nyt

import vaex as vx
import numpy as np
import textacy
from textacy import extract 
from functools import partial

import bpm.tex_idf as tex_idf


nlp = spacy.load("en_core_web_sm")
nlp.from_disk('project.nlp')

path = 'data/nyt_corpus/data/2000/01.spacy'


# %%


bin = DocBin(attrs=["LEMMA", "POS", "ENT_TYPE", "ENT_IOB"],store_user_data=True).from_disk(path)
docs = list(bin.get_docs(nlp.vocab))
en = textacy.load_spacy_lang("en_core_web_sm")

textlist = ["peter loves icecream, peter likes ducks","peter is going to the mall to eat icecream","the mall is big and peter loves it"]
docs = [textacy.make_spacy_doc(t, lang=en) for t in textlist]

for d in docs:
    print("_")
    for t in tex_idf.extract_terms(d):
        print(t.text)
#for f in test:
#    print(f)

#%%
tex_idf.generate_idf(nlp,docs)



#%%
result = tex_idf.get_tdidf(nlp,docs[1:4])

# %%
print(result[1])
print("HUH")
print(min(result[1]))
print(tex_idf.vectorizer.terms_list)

# %%
path = 'data/nyt_corpus/data/'

list_df = []
meta_df = {}
meta_df["id"] = []
meta_df["url"] = []
meta_df["date"] = []

id = 0
for root, dirs, files in os.walk(path):
    
    for f in files:
        if not f.endswith('.spacy'): continue
        
        p = os.path.join(root, f) #Get full path between the base path and the file
        bin = DocBin().from_disk(p)
        bin.store_user_data=True
        print("BIN")
        for doc in bin.get_docs(nlp.vocab):
            meta_df["id"].append(id)
            meta_df["url"].append(doc.user_data["url"])
            meta_df["date"].append(doc.user_data["date"])
            doc_data = doc.to_array(["LEMMA", "POS", "ENT_TYPE","ENT_IOB"])
            df = vx.from_arrays(
                article_id = np.full(doc_data.shape[0],id, dtype = np.int32),
                token_id = np.arange(doc_data.shape[0], dtype = np.int16),
                lemma=doc_data[:,0],
                pos=doc_data[:,1].astype("int8"),
                ent_type=doc_data[:,2].astype("int16"),
                ent_iob=doc_data[:,2].astype("int16")
            )
            id += 1
            list_df.append(df)
            

data_df = vx.concat(list_df)
data_df.export("data_df.hdf5")
meta_df = vx.from_dict(meta_df)
meta_df.export("meta_df.hdf5")


# %%
def translat2e(lemma):
    answer = nlp.vocab.strings[lemma]
    return answer

data_df = vx.open("data_df.hdf5")

grouped = data_df.groupby(
    ["lemma"],
    agg={ "cnt": vx.agg.count()}
)
grouped.sort("cnt",ascending=False)

#%%
grouped_small = grouped[0:100]
print(grouped_small)
grouped_small["word"] = grouped_small.apply(translat2e, arguments=[grouped_small.lemma])
grouped_small
# %%
a = translat2e(8228585124152053988)
a
nlp.vocab.strings[8228585124152053988]

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
