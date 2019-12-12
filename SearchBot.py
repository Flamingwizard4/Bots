## ResearchBot
# A program to facilitate research, meaning Google search + web scraping + content compilation + LP summarization
# TODO:
# check robots.txt for specs
# add some random sleep, clicks, movement, actions
# rotate IPs, proxies, user agents, use headless browser
# avoid honey pots and logins
# add depth option for recursive search
# test TokenBot and potentially fuse approaches
# make priority queue with value function using content similarity to corpus
# use gradient extraction coefficient (default: linear) to create dataset to train TransformerXL, default is 100% of layer 0, top 90% of layer 1, top 80% of layer 2, etc. to layer 9
# use exponential gradient
##

#pip install bs4, requests, scholarly, html5lib, google, progressbar2, clint, selectolax, warc, spacy, nltk, etc.
import sys, os, progressbar, time #utilities
import re #Regex URL Validation
import shutil, tempfile #copying files
#import warc #file format for storing web crawls as sequences of content blocks
import argparse #command line arguments
import requests #HTTP request
import scholarly #Google Scholar search
import webbrowser #open URL in browser

from googlesearch import search #Google Search results list
from clint.textui import progress #download progress bar
from io import BytesIO 
#below doesn't work
import TokenBot # import * #HTML Parsers, clean-up, and tokenizers

"""METHODS"""

#URL Validation
def URLV(regex, qry, dn, sn): #URL regex, search query, depth num, and search num
    if qry is None:
        print("Empty query. Exiting...")
        exit()
    elif re.match(regex, qry):
        print("Search query: ", query)
        q = input("Your search query is a website, do you want to go straight to the URL?? Enter yes/no: ")
        if re.match(q, "yes"):
            webbrowser.open(qry)
        elif re.match(q, "no"):
            results = search_query(qry, sn)
        else:
            URLV(regex, qry)
    else:
        print("Search query: ", query)
        results = search_query(qry, sn)

#returns googlesearch generator        
def search_query(qry, resnum):
    print("Searching...")
    #variable number of search results
    link_gen = search(qry, num=resnum, pause=2)

#gets layer 0 URLs, saves them to storepath, extracts their links and content, and returns both as lists
def get_search_results(results, storepath, tok_list):
    URLcount = 0
    URL_list = []
    with open(storepath,"w") as sh:
        sh.write("Query: " + query + "\n\n")
        for link in results: #Search gen 
            time.sleep(0.2)  #is this really necessary?? I'll leave it for now.
            URL_list.append(link)
            sh.write(link + "\n") #writing layer 0 URLs
            sh.flush()
            extract_content_from_URL(link, tok_list)
            URLcount += 1 
    return URL_list           

#ensures the response has a Content-Length header
def ensure_content_length(
    url, *args, method='GET', session=None, max_size=2**20,  # 1Mb
    **kwargs):
    kwargs['stream'] = True
    session = session or requests.Session()
    r = session.request(method, url, *args, **kwargs)
    if 'Content-Length' not in r.headers:
        # stream content into a temporary file so we can get the real size
        spool = tempfile.SpooledTemporaryFile(max_size)
        shutil.copyfileobj(r.raw, spool)
        r.headers['Content-Length'] = str(spool.tell())
        spool.seek(0)
        # replace the original socket with our temporary file
        r.raw._fp.close()
        r.raw._fp = spool
    return r

#extracts and returns list of sentences from URL link and list of tokenizer functions
def extract_content_from_URL(link, tok_list):
    r = ensure_content_length(link) #ensures the response has a Content-Length header 
    contentLen = int(r.headers["Content-Length"]) #not len(r.raw.read())
    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(contentLen/1024) + 1): 
        if chunk:
            with open(wcontentpath,"w") as cp: #using bs4
                #cp.write(chunk)
                txt = get_text_bs(r.content)
                    
                    
            with open(bcontentpath,"w") as cp2: #using selectolax
                #cp.write(chunk)
                txt = get_text_selectolax(r.content)
                if txt:
                    for s in clean_text(txt):
                        if not s.isspace() and not s in seensent:
                            cp2.write(txt)
                            cp2.flush()
                            seensent.add(s)

def read_data(storepath, wlcontentpath, blcontentpath):      
    with open(storepath, "r") as hreader:
        for line in hreader:
            print(line)

    with open(wcontentpath, "r") as wlcreader:
        for line in wlcreader:
            print(line)

    with open(bcontentpath, "r") as blcreader:
        for line in blcreader:
            print(line)

def extract_content(path, txt):
    sentences = []
    seensent = set() #set of seen sentences to avoid duplicates
    if txt:
        text = ""
        for s in TokenBot.clean_text(txt): #should I strip this and append everything to one string with spaces? what about paragraphs?
            text += s #compile all text at URL after preprocessing
        paras = [para for para in text.strip().splitlines() if para] #should separate all text into paragraphs
        for p in paras: #for paragraph in paragraphs
            tokcount = 0
            for tok in tok_list:
                for sent in TokenBot.tok(p):
                    if not (sent in seensent):
                        placeH = ("Using extraction method #%d: " % tokcount) #displaying which tokenizer
                        path.write(placeH + sent) #write all sentences in paragraph for each tokenizer
                        path.flush()
                        seensent.add(sent)
                tokcount += 1
    return sentences            

"""FREE CODE"""

#initializing variables
cdir = os.getcwd()
storepath = os.path.join(cdir, "links.txt") #search.txt file in working directory
wcontentpath = os.path.join(cdir, "wcontent.txt") #content.txt file in working dir
bcontentpath = os.path.join(cdir, "bcontent.txt") #content2.txt file in working dir
tok_list = []

#receive query from command line, e.g. os.system("python3 SearchBot.py quicksort -r 5 -n 15 &")
psr = argparse.ArgumentParser()
psr.add_argument("q", type=str, help="search query", metavar="query", nargs="*")
psr.add_argument("-d", type=int, help="depth of search", metavar="depth")
psr.add_argument("-n", type=int, help="number of results to search", metavar="number")
args = psr.parse_args()
query = None
depth = 10
rnum = 1000
if args.q:
    query = str(args.q) #don't think I need str, or ints here
if args.d:
    depth = int(args.d)
if args.n:
    rnum = int(args.n)

#URL Validation Regular Expression
URLregex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

print("Current working directory: ", cdir,  "\n")
URLV(URLregex, query, rnum)
print("\nDone.")
