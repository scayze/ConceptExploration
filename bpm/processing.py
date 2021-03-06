#
# This file handles the preprocessing of the corpus
#

import spacy
from spacy.tokens import DocBin
import tarfile
import bpm.nyt_corpus as nyt

# Preprocesses the archieve passed in.
def process_archieve(nlp,path = ""):  
    print("PREPROCESSING: " + path)
    user_data = []
    list_document = []

    with tarfile.open(path, 'r:*') as tar:

        for inner_file in tar:
            # Skip everything but the articles
            if not inner_file.name.endswith(".xml"): continue
            # Extract single document
            content = tar.extractfile(inner_file).read().decode('utf8')
            url, date, doc = nyt.read_nitf_file(content)
            # Append data
            if doc == "": continue
            meta = {"url": url, "date": date}
            user_data.append(meta)
            list_document.append(doc)

    doc_bin = DocBin(attrs=["LEMMA", "POS", "ENT_TYPE", "ENT_IOB"],store_user_data=True)
    
    i=0
    for doc in nlp.pipe(list_document,n_process=4,batch_size=100):
        doc.user_data = user_data[i]
        doc_bin.add(doc)
        i+=1

    nlp.to_disk("nlpnlpnlp")
    doc_bin.to_disk(path[:-4] + ".spacy")