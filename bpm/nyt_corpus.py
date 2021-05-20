import pickle
import numpy as np
import pandas as pd
import os
import sys
import regex as re
import co_occurance as co
import pickle 
#import scipy
import xml.etree.ElementTree as ET
from pathlib import Path
import glob
import tools
from datetime import datetime
import time
import threading
import vaex as vx
import tarfile

re_special_characters = re.compile(r"[^a-z]+")


def read_nitf_file(path,dist = "file"):
    tree = ET.parse(path)
    root = tree.getroot()
    content = root.find("body/body.content")

    
    paragraphs = []
    for block in content:
        if block.get("class") != "full_text": continue
        
        par_list = block.findall("p")
        for p in par_list:
            text = re.sub(re_special_characters, ' ', p.text.lower())
            if(len(text) > 4): paragraphs.append(text)

    if dist == "par":
        return paragraphs
    elif dist == "docs":
        return [" ".join(paragraphs)]
    elif dist == "file":
        return [" ".join(paragraphs)]

def read_nitf_file_doc(path):
    tree = ET.parse(path)
    root = tree.getroot()
    content = root.find("body/body.content")
    #print(content)

    for block in content:
        if block.get("class") != "full_text": continue
        
        par_list = [p.text for p in block.findall("p")]
        text = " ".join(par_list)
        text = re.sub(re_special_characters, ' ', text.lower())
        #print(text)
        return [text]
    return []

def read_nitf_folder(path,dist):
    parts = []
    files = os.listdir(path)
    for f in files:
        if not f.endswith(".xml"): continue
        #print("PATH: ",path + f)
        parts += read_nitf_file(path + f,"par")
        #parts += read_nitf_file_doc(path + f)
    
    if dist == "par":
        return parts
    elif dist == "docs":
        return parts
    elif dist == "file":
        return [" ".join(parts)]

def clean_corpus():
    path = 'data/nyt_corpus/data/'
    endings = [".bz2",".gzip",".pkl",".npz",".csv",".pkt"]

    prompt = " [YES/NO] "
    question = "THIS WILL DELETE ALL FILES WITH THE TYPES " + " ".join(endings) + " FOUND IN THE CORPUS"
    while True:
        sys.stdout.write(question + prompt)
        choice = input()
        if choice == "YES":
            break
        elif choice == "NO":
            return
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' " "(or 'y' or 'n').\n")

    for e in endings:
        files = glob.glob(path + '**/*' + e, recursive=True)
        
        for f in files:
            try:
                print(f)
                os.remove(f)
            except OSError as e:
                print("Error: %s : %s" % (f, e.strerror))

def generate_day_data():
    path = 'data/nyt_corpus/data/'

    year_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    year_split = tools.split(year_folders,4)
    year_split = list(year_split)[1:]
    threads = []

    for s in year_split:
        print("WHAT: ",s)
        t = threading.Thread(target=generate_day_year, args=(s,))
        threads.append(t)
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("SUCCESSS WOOOO")

#GENERATE ONE FILE VAEX
def read_nitf_file_vx(content,backend = "vaex"):
    tree = ET.fromstring(content)
    root = tree #.getroot()

    #Get publication data
    pub_data = root.find("head/pubdata")

    pub_url = pub_data.get("ex-ref")

    pub_date = pub_data.get("date.publication")
    if backend == "vaex":
        pub_date = np.datetime64(datetime.strptime(pub_date[0:8],"%Y%m%d")) # Datetime example: 20070512T000000, thus we strip everything but the first 8 characters, as timestamp is irrelevant
    elif backend == "pandas":
        pub_data = pd.to_datetime(pub_date[0:8],format="%Y%m%d")
    #Get All text paragraphs from content
    content = root.find("body/body.content")

    for block in content:
        if block.get("class") != "full_text": continue
        
        par_list = [p.text for p in block.findall("p")]
        text = " | ".join(par_list).lower()
        return pub_url, pub_date, text
    return pub_url, pub_date, "" #Return empty text if none was found

def generate_data_year_vx(year_folders,results,i,backend):
    print(year_folders)
    path = 'data/nyt_corpus/data/'

    list_url = []
    list_date = []
    list_document = []
    list_file = []

    for folder_year in year_folders:
        print("NOW: " + str(folder_year))
        for root, dirs, files in os.walk(folder_year):
            for f in files:
                if not f.endswith('.tgz'): continue
                p = os.path.join(root, f)

                with tarfile.open(p, 'r:*') as tar:
                    for inner_file in tar:
                        filename = inner_file.name
                        # Skip everything but the articles
                        if not filename.endswith(".xml"):
                            continue
                        content = tar.extractfile(inner_file).read().decode('utf8')
                        url, date, doc = read_nitf_file_vx(content,backend)
                        list_url.append(url)
                        list_date.append(date)
                        list_document.append(doc)
                        list_file.append(p)

    if backend == "vaex":
        url_column = np.array(list_url)
        date_column = np.array(list_date)
        data_column = np.array(list_document,dtype=object)
        file_column = np.array(list_file)
                
        results[i] = vx.from_arrays(url = url_column, date = date_column, article = data_column, filepath=file_column)

    elif backend == "pandas":
        results[i] = pd.DataFrame.from_dict({"url": list_url,"date": list_date, "filepath": list_file, "textdata": list_document})
        pass


def generate_data_year_vx2(year_folders,results,i,backend):
    print(year_folders)
    path = 'data/nyt_corpus/data/'


    for folder_year in year_folders:
        print("NOW: " + str(folder_year))
        for root, dirs, files in os.walk(folder_year):
            for f in files:
                if not f.endswith('.tgz'): continue
                p = os.path.join(root, f)

                with tarfile.open(p, 'r:*') as tar:
                    list_url = []
                    list_date = []
                    list_document = []
                    list_file = []

                    for inner_file in tar:
                        filename = inner_file.name
                        # Skip everything but the articles
                        if not filename.endswith(".xml"):
                            continue
                        content = tar.extractfile(inner_file).read().decode('utf8')
                        url, date, doc = read_nitf_file_vx(content,backend)
                        list_url.append(url)
                        list_date.append(date)
                        list_document.append(doc)
                        list_file.append(p)
                    df = pd.DataFrame.from_dict({"url": list_url,"date": list_date, "filepath": list_file, "textdata": list_document})
                    new_path = os.path.join(root, f.split(".")[0] + ".pck")
                    df.to_pickle(str(new_path))

def generate_day_data_vx(backend = "vaex"):
    path = 'data/nyt_corpus/data/'
    num_threads = 4
    year_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    year_split = list(tools.split(year_folders,num_threads))
    threads = [None] * num_threads
    results = [None] * num_threads

    for i in range(0,num_threads):
        threads[i] = threading.Thread(target=generate_data_year_vx, args=(year_split[i],results,i,backend))
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    if backend == "vaex":
        data_df = vx.concat(results)
        data_df.export_hdf5("vx_data.hdf5")
    elif backend == "pandas":
        data_df = pd.concat(results)
        data_df.set_index(["date"])
        data_df.index = pd.to_datetime(data_df.index)
        data_df.to_pickle("pd_data.pck")
    
    print("SUCCESSS WOOOO")


def generate_day_data_vx2(backend = "vaex"):
    path = 'data/nyt_corpus/data/'
    num_threads = 4
    year_folders = [f.path for f in os.scandir(path) if f.is_dir()]
    year_split = list(tools.split(year_folders,num_threads))
    threads = [None] * num_threads
    results = [None] * num_threads

    for i in range(0,num_threads):
        threads[i] = threading.Thread(target=generate_data_year_vx2, args=(year_split[i],results,i,backend))
    
    for t in threads:
        t.start()

    for t in threads:
        t.join()
    
    print("SUCCESSS WOOOO")

def get_data_between_pd(term,date_from,date_to):
    print("load")
    path = 'data/nyt_corpus/data/'
    df_list = []

    for root, dirs, files in os.walk(path):
        
        for f in files:
            if not f.endswith('.pck'): continue
            
            p = os.path.join(root, f)
            
            date = pd.to_datetime(p[len(path):-4])    #convert filepath to a datetime object.
            if date < date_from or date >= date_to: continue      #filter if date is not withon [from:to]
            print(date)
            df = pd.read_pickle(p)    #read the data of the current day
            df_list.append(df)                          #append d


    print("concat")
    df = pd.concat(df_list)
    print("drop")
    if term != "":
        df = df[df["textdata"].str.contains(term)]
    #tools.parallelize_on_rows(df["data"],termify)
    #print("save")
    df.to_csv("HahsdhashdhAS.csv")
    return df

if __name__ == '__main__':
    generate_day_data_vx2(backend = "pandas")
    pass
    #aaaaa = pd.read_pickle("pd_data.pck")