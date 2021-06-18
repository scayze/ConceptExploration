from logging import Handler
import os
import sys
import glob

import bpm.tools as tools

import xml.etree.ElementTree as ET
import pandas as pd

import spacy
import spacy.attrs

from spacy.tokens import DocBin

from textacy import extract
from functools import partial
import itertools

# Just a function that cleans the corpus folder from unnecessary files i created at some point for testing and such
def clean_corpus():
    path = 'data/nyt_corpus/data/'
    endings = [".spacy"]

    prompt = " [YES/NO] "
    question = "THIS WILL DELETE ALL FILES WITH THE TYPES " + " ".join(endings) + " FOUND IN THE CORPUS"
    while True:
        sys.stdout.write(question + prompt)
        choice = input()
        if choice == "YES": break
        elif choice == "NO": return
        else: sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

    for e in endings:
        files = glob.glob(path + '**/*' + e, recursive=True)
        
        for f in files:
            try:
                print("Removing file: ", f)
                os.remove(f)
            except OSError as e:
                print("Error: %s : %s" % (f, e.strerror))


# Read an xml file from the corpus as string, and extract all relevant information
def read_nitf_file(content):
    #Parse file contents
    tree = ET.fromstring(content)

    #Get publication data
    pub_data = tree.find("head/pubdata")
    pub_url = pub_data.get("ex-ref")
    pub_date = pub_data.get("date.publication")
    
    # Datetime example: 20070512T000000, thus we strip everything but the first 8 characters, as timestamp is irrelevant
    #pub_date = np.datetime64(datetime.strptime(pub_date[0:8],"%Y%m%d")) 
    pub_data = pd.to_datetime(pub_date[0:8],format="%Y%m%d")

    #Get All text paragraphs from content
    content = tree.find("body/body.content")

    for block in content:
        #Skip articles without text
        if block.get("class") != "full_text": continue
        #Concatenate paragraphs with newline
        par_list = [p.text for p in block.findall("p")]
        text = "\n ".join(par_list)
        return pub_url, pub_date, text
    return pub_url, pub_date, "" #Return empty text if none was found


# Extract all relevant features from a spacy document, and preprocess them.
# Currently:
#   Entities of type: ["PERSON","ORG","NORP","FAC","GPE","LOC","PRODUCT","EVENT"]
#   2grams
def extract_terms(doc):
    terms = extract.terms(  
        doc,
        ngs=lambda doc: extract.ngrams(
            doc,
            n=[2],
            filter_nums=True,
            filter_punct=True,
            filter_stops=True,
        ),
        ents=partial(
            extract.entities, 
            include_types=["PERSON","ORG","NORP","FAC","GPE","LOC","PRODUCT","EVENT"]
        )
    )
    return [term.text.lower() for term in terms]

def get_raw_docs(date_from,date_to):
    print("LOADING RAW DOCS")
    path = 'data/nyt_corpus/data/'
    nlp = spacy.load("en_core_web_sm")
    nlp.from_disk('nlpnlpnlp')

    file_handles = []
    for root, dirs, files in os.walk(path):
        
        for f in files:
            if not f.endswith('.spacy'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            date = pd.to_datetime(p[len(path):-6]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)
            file_handles.append(p)
    
    return (
        DocBin(store_user_data=True).from_disk(handle).get_docs(nlp.vocab)
        for handle
        in file_handles
    )


def get_data_generator(date_from,date_to):
    print("LOADING RAW DOCS")
    path = 'data/nyt_corpus/data/'

    file_handles = []

    for root, dirs, files in os.walk(path):
        
        for f in files:
            if not f.endswith('.pck'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            date = pd.to_datetime(p[len(path):-4]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)
            file_handles.append(p)
    #single_list = itertools.chain.from_iterable(doc_list["textdata"])
    return (itertools.chain.from_iterable(pd.read_pickle(handle)["textdata"]) for handle in file_handles)


def get_data_generator_between(date_from,date_to):
    path = 'data/nyt_corpus/data/'
    file_handles = []

    for root, dirs, files in os.walk(path):
        
        for f in files:
            if not f.endswith('.pck'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            date = pd.to_datetime(p[len(path):-4]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            file_handles.append(p)

    return (
        pd.read_pickle(handle)
        for handle 
        in file_handles
    )


def generate_term_dfs(date_from = pd.to_datetime("1970"), date_to = pd.to_datetime("2020")):
    print("EXTRACTING DATA")
    path = 'data/nyt_corpus/data/'
    nlp = spacy.load("en_core_web_sm")
    nlp.from_disk('nlpnlpnlp')

    for root, dirs, files in os.walk(path):
        for f in files:
            if not f.endswith('.spacy'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file

            date = pd.to_datetime(p[len(path):-6]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)

            bin = DocBin(store_user_data=True).from_disk(p)
            docs = bin.get_docs(nlp.vocab)

            token_lists = []
            date_list = []
            url_list = []
            for doc in docs:
                tokens = extract_terms(doc)
                token_lists.append(tokens)
                date_list.append(doc.user_data["date"])
                url_list.append(doc.user_data["url"])
            
            df = pd.DataFrame.from_dict({"date":date_list, "url":url_list, "textdata":token_lists})
            df = df.set_index("date")
            tools.make_index_unique(df)
            new_filename = f.split(".")[0] +".pck"
            df.to_pickle(os.path.join(root, new_filename))
