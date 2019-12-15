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
#apt install scrot
import sys, os, progressbar, time #utilities
import re #Regex URL Validation
import shutil, tempfile #manipulating files
#import warc #file format for storing web crawls as sequences of content blocks
import argparse #command line arguments
import requests #HTTP request
import scholarly #Google Scholar search
import webbrowser #open URL in browser

from googlesearch import search #Google Search results list
from clint.textui import progress #download progress bar
from io import BytesIO #
from lxml.html import fromstring #proxy parser
from TokenBot import * #HTML Parsers, clean-up, and tokenizers

"""METHODS"""
#URL Validation, returns result generator
def URLV(regex, qry):
    if qry is None:
        print("Empty query. Exiting...")
        exit()
    print("Search query: ", query)    
    if re.match(regex, qry):
        q = input("Your search query is a website, do you want to go straight to the URL?? Enter yes/no: ")
        if re.match(q, "yes"):
            webbrowser.open(qry)
        elif re.match(q, "no"):
            pass
        else:
            URLV(regex, qry)

#returns googlesearch generator        
def search_query(qry, resnum):
    print("Searching...")
    #variable number of search results
    link_gen = search(qry, num=resnum, pause=2)    

#gets layer 0 URLs, extracts their links and content, and iterates, saving to storepath
def save_search_results(resgen, spath, toks, dep, prox):
    #URLcount = 0
    URL_list = []
    for d in range(dep):
        layerpath = os.path.join(spath, "layer%d"%d)
        os.mkdir(layerpath)
        with open(os.path.join(layerpath, "links%d.txt"%d),"w") as sh:
            if d == 0:
                sh.write("Query: " + query + "\n\n")
                for link in resgen: #Search gen 
                    time.sleep(0.2)  #is this really necessary?? I'll leave it for now.
                    sh.write(link + "\n")
                    sh.flush()
                    ws, bs, urls = extract_content_from_URL(link, toks, prox)
                    for u in urls:
                        URL_list.append(u)
                        #URLcount += 1
                    #URLcount += 1
                    with open(os.path.join(layerpath, "whitelisted_%s"%link)) as wcontent:
                        wcontent.writelines(ws) #do I need to iterate through the lines??
                        wcontent.flush()
                    with open(os.path.join(layerpath, "blacklisted_%s"%link)) as bcontent:
                        bcontent.writelines(bs)
                        bcontent.flush()        
            else:
                sh.write("\n\n Layer %d: \n\n")
                layerlinks = URL_list.copy()
                URL_list = []
                for l in layerlinks:
                    sh.write(l + "\n")
                    sh.flush()
                    ws, bs, urls = extract_content_from_URL(l, toks, prox)
                    for u in urls:
                        URL_list.append(u)
                        #URLcount += 1
                    with open(os.path.join(layerpath, "whitelisted_%s"%link)) as wcontent:
                        wcontent.writelines(ws) #do I need to iterate through the lines??
                        wcontent.flush()
                    with open(os.path.join(layerpath, "blacklisted_%s"%link)) as bcontent:
                        bcontent.writelines(bs)
                        bcontent.flush()    

#ensures the response has a Content-Length header, PAY ATTENTION TO THIS METHOD HEADER
def ensure_content_length(
    url, *args, method='GET', session=None, max_size=2**20,  # 1Mb
    **kwargs):
    kwargs['stream'] = True
    session = session or requests.Session()
    r = session.request(method, url, *args, **kwargs) #hope this works with proxies passed in
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

#extracts and returns list of whitelisted sentences, blacklisted sentences, & links from URL
def extract_content_from_URL(URL, toks, prox):
    sentences, links = []
    seenlink = set()
    r = ensure_content_length(URL, prox) #ensures the response has a Content-Length header 
    contentLen = int(r.headers["Content-Length"]) #not same as len(r.raw.read())
    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(contentLen/1024) + 1): 
        if chunk: 
            #using bs4 whitelisting
            wtxt, wlinks = get_text_bs(r.content)
            wsents = extract_sentences(wtxt, toks)    
            #using selectolax whitelisting
            btxt, blinks = get_text_selectolax(r.content)
            bsents = extract_sentences(btxt, toks)
            for w in wlinks:
                if not (w in seenlink):
                    seenlink.add(w)
                    links.append(w)
            for b in blinks:
                if not (b in seenlink):
                    seenlink.add(b)
                    links.append(b)        
    return wsents, bsents, links        

#parses sentences from filtered HTML txt using multiple tokenizers to return list
def extract_sentences(txt, toks):
    sentences = []
    seensent = set() #set of seen sentences to avoid duplicates
    if txt:
        text = ""
        for s in clean_text(txt): #should I strip this and append everything to one string with spaces? what about paragraphs?
            text += s #compile all text at URL after preprocessing
        paras = [para for para in text.strip().splitlines() if para] #should separate all text into paragraphs
        for p in paras: #for paragraph in paragraphs
            tokcount = 0
            for tok in toks:
                for sent in globals()[tok](p):
                    if not (sent in seensent):
                        placeH = ("Using extraction method #%d: " % tokcount) #displaying which tokenizer for debug purposes
                        sentences.append([placeH + sent])
                        seensent.add(sent)
                tokcount += 1
    return sentences            

#prints links/content
def read_data(stpath):      
    #goes through all links, then all content
    pass

#scrapes and returns list of proxies, default is "https://free-proxy-list.net"
def get_proxies(URL):
    if URL:
        url = URL
    else:
        url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr')[:10]:
        if i.xpath('.//td[7][contains(text(),"yes")]'):
            #Grabbing IP and corresponding PORT
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxies.add(proxy)
    return proxies

"""FREE CODE"""
#initializing variables
cdir = os.getcwd()
storepath = os.path.join(cdir, "search") #path for storing search URLs/content
if os.isdir(storepath): #clear storepath
    shutil.rmtree(storepath)
os.mkdir(storepath)
proxies = get_proxies()
tok_list = ["extract_sentences2", "extract_sentences_smart"]
testURL = "https://en.wikipedia.org/wiki/Machine_learning"

#receive query from command line, e.g. os.system("python3 SearchBot.py quicksort -r 5 -n 15 &")
psr = argparse.ArgumentParser()
psr.add_argument("q", type=str, help="search query", metavar="query", nargs="*")
psr.add_argument("-d", type=int, help="depth of search", metavar="depth")
psr.add_argument("-n", type=int, help="number of results to search", metavar="number")
psr.add_argument("-m", type=bool, help="multiple query search", metavar="multiple")
args = psr.parse_args()
query = None
depth = 10
rnum = 1000
mult = False
if args.q:
    query = str(args.q) #don't think I need str, or ints here
if args.d:
    depth = int(args.d)
if args.n:
    rnum = int(args.n)
if args.m:
    mult = True    

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
save_search_results(search_query(query, rnum), storepath, tok_list, depth, proxies)
print("\nDone.")
