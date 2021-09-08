#
# This file contains all functions related to receiving data from, or processing, the corpus.
#

import os
import sys
import glob
import re

from collections import Counter

import bpm.tools as tools
import bpm.tf_idf as tf

import xml.etree.ElementTree as ET
import pandas as pd

import spacy
from spacy.tokens import DocBin

import pandas as pd
import numpy as np

import tarfile

from scipy.sparse import csr_matrix

from textacy import extract
from functools import partial

all_data = None

# Just a function that cleans the corpus folder from unnecessary files i created at some point for testing and such
def clean_corpus(endings):
    path = 'data/nyt_corpus/data/'

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
#   bigrams
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

# This method extracts all occurances of a term in the corpus, given a time period.
# It returns a list of dictionaries, each representing an occurance found in the article texts.
# date_from, date_to: The date range
# filter: The term that is required to be present in the document to return results (the search term)
# term: The term we check for occurances for
def keyword_in_context(date_from,date_to,filter,term,limit):
    path = 'data/nyt_corpus/data/'
    file_handles = []

    #Generate a list of all file handles from the files containing data in the right timeperiod
    for root, dirs, files in os.walk(path):
        for f in files:
            if not f.endswith('.cnc'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            date = pd.to_datetime(p[len(path):-4]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)
            file_handles.append(p)
    
    #Find occurances in the corpus
    output = []
    for handle in file_handles:
        df = pd.read_pickle(handle)
        # Filter to only leave the articles that contain both the search term (filter), and the detail term (term)
        df = df.loc[df["fulltext"].str.contains(filter,case=False,regex=False)]

        for row in df.itertuples():
            url = row.url
            content = row.fulltext

            occurance_idx = [m.start() for m in re.finditer(term, content, re.IGNORECASE)]
            for idx in occurance_idx:
                #Take a sample of the article in which the occurance happened.
                sample_length = 150
                left_from = max(0, idx - sample_length)
                left_to = idx
                right_from = idx + len(term)
                right_to = idx + min(len(content), len(term) + sample_length)
                
                occurance_dict = {}
                occurance_dict["left"] = content[left_from:left_to]
                occurance_dict["kwiq"] = term
                occurance_dict["right"] = content[right_from:right_to]
                occurance_dict["url"] = url
                output.append(occurance_dict)
                # If the desired amount of results has been found, stop and return the results
                if len(output) >= limit: return output
    return output

# This function returns a generator that iteratively returns the rows of a list of dataframes.
def get_doc_generator_between(date_from,date_to):
    data_generator = get_data_generator_between(date_from,date_to)
    return (
        row
        for df 
        in data_generator
        for row
        in df["textdata"]
    )

# This function returns a generator that iteratively returns a dataframes betweens a timerange
def get_data_generator_between(date_from,date_to):
    #global all_data
    #if all_data is None:
    #    all_data = pd.read_pickle("all_data.pck")
    #return  [all_data.loc[date_from:date_to]]
    path = 'data/nyt_corpus/data/'
    file_handles = []

    for root, dirs, files in os.walk(path):
        
        for f in files:
            if not f.endswith('.pck_sparse'): continue
            p = os.path.join(root, f) #Get full path between the base path and the file
            date = pd.to_datetime(p[len(path):-11]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            file_handles.append(p)

    return (
        pd.read_pickle(handle)
        for handle 
        in file_handles
    )


# This function extracts features from each document, and saves them to a pandas DataFrame
def generate_term_dfs(date_from = pd.to_datetime("1970"), date_to = pd.to_datetime("2020")):
    print("Extracting features from SpaCy files")

    #Load the spacy pipe and its config from disk.
    nlp = spacy.load("en_core_web_sm")
    nlp.from_disk('nlpnlpnlp')

    # Walk across all files in the directory
    path = 'data/nyt_corpus/data/'
    for root, dirs, files in os.walk(path):
        for f in files:
            #Ignore all non spacy files
            if not f.endswith('.spacy'): continue 

            #Construct the full paths of the spacy file, and the path to which to save the processed data
            p = os.path.join(root, f) 
            new_filename = f.split(".")[0] +".pck"
            new_path = os.path.join(root, new_filename)

            if os.path.isfile(new_path): continue

            #Convert the part of the path that denotes the date, to a datetime object.
            #Only continue processing it if its within the specified timerange
            date = pd.to_datetime(p[len(path):-6]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)

            #Load docs from disk
            bin = DocBin(store_user_data=True).from_disk(p)
            docs = bin.get_docs(nlp.vocab)

            #Extract tokens and dates from the SpacyDocs
            token_lists = []
            date_list = []
            for doc in docs:
                tokens = extract_terms(doc)
                token_lists.append(tokens)
                date_list.append(doc.user_data["date"])
            
            #Create a new DataFrame from the data, generate a DateTimeIndex, and make the index unique
            df = pd.DataFrame.from_dict({"date":date_list, "textdata":token_lists})
            df.set_index("date",inplace=True)
            tools.make_index_unique(df)

            df.to_pickle(new_path)

# This function generates the pandas dataframe that contains a sparse matrix containing all the features. 
# This results in significantly smaller filesize, and a datastructure that is faster to compute TFIDF scores with.
def generate_sparse_term_dfs(date_from = pd.to_datetime("1970"), date_to = pd.to_datetime("2020")):
    print("Creating sprase feature DataFrames")

    # Walk across all files in the directory
    path = 'data/nyt_corpus/data/'
    for root, dirs, files in os.walk(path):
        for f in files:
            #Ignore all non spacy files
            if not f.endswith('.pck'): continue 

            #Construct the full paths of the spacy file, and the path to which to save the processed data
            p = os.path.join(root, f) 
            new_filename = f.split(".")[0] +".pck_sparse"
            new_path = os.path.join(root, new_filename)

            if os.path.isfile(new_path): continue

            #Convert the part of the path that denotes the date, to a datetime object.
            #Only continue processing it if its within the specified timerange
            date = pd.to_datetime(p[len(path):-4]) #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue #filter if date is not within [from:to]
            print(date)

            df = pd.read_pickle(p)

            # Inner function that defines the process of converting a feature list to a sparse count matrix
            def to_sparse(wordlist):
                # Create a list of indices from the feature names
                id_list = [tf.word2id[word] for word in wordlist if word in tf.word2id] 

                # Count the features
                c = Counter(id_list)
                keys = list(c.keys())
                vals = list(c.values())

                # Generate a csr matrix with the length of our vocabulary, with our counted features filled in
                cols = np.array(keys)
                rows = np.zeros(len(keys),dtype=np.int32)
                data = np.array(vals)

                matrix = csr_matrix(
                    (data,(rows,cols)),
                    shape=(1,len(tf.idf)),
                    dtype=np.int32
                )
                return matrix

            #Apply the function to the dataframe, and save it to disk.
            df["textdata"] = df["textdata"].apply(to_sparse)
            df.to_pickle(new_path)

#This function extracts all full texts of the articles from the corpus, and saves them together with the articles URL in the rows of a pandas DataFrame
def generate_concodrance_files():
    path = 'data/nyt_corpus/data/'
    for root, dirs, files in os.walk(path):
        for f in files:
            if not f.endswith('.tgz'): continue

            file_no_extension = f[:-4]
            file_pck = file_no_extension + ".cnc"

            p = os.path.join(root, f) #Get full path between the base path and the file
            path_cdc = os.path.join(root, file_pck)

            print(p)

            doclist = []
            urllist = []
            with tarfile.open(p, 'r:*') as tar:
                for inner_file in tar:
                    # Skip everything but the articles
                    if not inner_file.name.endswith(".xml"): continue
                    # Extract single document
                    
                    content = tar.extractfile(inner_file).read().decode('utf8')
                    url, date, doc = read_nitf_file(content)
                    if doc == "": continue
                    doclist.append(doc)
                    urllist.append(url)
            df = pd.DataFrame.from_dict({"url":urllist, "fulltext":doclist})
            df.to_pickle(path_cdc)