## ResearchBot
# A program to facilitate research, meaning Google search + web scraping + content compilation + NLP summarization
# TODO:
# check robots.txt for specs
# add some random sleep, clicks, movement, actions
# user agents, use headless browser
# avoid honey pots and logins
# add website prowling
#
# make priority queue with value function using content similarity to corpus
# use gradient extraction coefficient (default: linear) to create dataset to train TransformerXL, default is 100% of layer 0, top 90% of layer 1, top 80% of layer 2, etc. to layer 9
# use exponential gradient
#
# add -t option for specific HTML tags? e.g. links/content/images
# add -s option for selective screencapture
##

#pip install bs4, requests, scholarly, html5lib, google, progressbar2, clint, selectolax, warc, spacy, nltk, etc.
#apt install scrot
import sys, os, progressbar, time #utilities
import re, PIL #Regex URL Validation
import shutil, tempfile #manipulating files
#import warc #file format for storing web crawls as sequences of content blocks
import argparse #command line arguments
import requests #HTTP request
import scholarly #Google Scholar search
import webbrowser #open URL in browser
#import pyautogui #screenshot

from googlesearch import search #Google Search results list
from clint.textui import progress #download progress bar
from io import BytesIO #
from lxml.html import fromstring #proxy parser
import TokenBot
from TokenBot import * #HTML Parsers, clean-up, and tokenizers
from PIL import Image
from itertools import cycle
from urllib.parse import urlparse

"""METHODS"""
#URL Validation, returns result generator
def URLV(regex, qry, savepath, toks):
    if not qry:
        print("Empty query.")
    else:
        print("Search query: ", query)    
        if not mult and re.match(regex, qry):
            q = input("Your search query is a website, do you want to go straight to the URL?? Default no: ")
            if re.match(q, "no") or not q or re.match(q, "n"): #does this need an escape character?
                q2 = input("Do you want to only search this site?? Default yes: ")
                if re.match(q2, "yes") or not q2 or re.match(q2, "y"):
                    with open(os.path.join(savepath, "links.txt"), "w") as sp:
                        links = save_results(savepath, qry, toks)
                        for u in links:
                            sp.write(u + "\n")
                            sp.flush()
                elif re.match(q2, "no") or re.match(q2, "n"):
                    searchflag = True
                else:
                    URLV(regex, qry, savepath, toks)
            elif re.match(q, "yes") or re.match(q, "y"):
                webbrowser.open(qry, new=2)
            else:
                URLV(regex, qry, savepath, toks)
        else:
            searchflag = True
     
#returns googlesearch generator        
def search_query(qry, resnum):
    print("Searching...")
    #variable number of search results
    return search(qry, num=resnum, pause=2)    

#gets layer 0 URLs, extracts their links and content, and iterates, saving to storepath
def save_search_results(resgen, spath, dep, toks):
    #URLcount = 0
    URL_list = []
    for d in range(dep):
        layerpath = os.path.join(spath, "layer%d"%d)
        os.mkdir(layerpath)
        with open(os.path.join(layerpath, "links%d.txt"%d),"w") as sh:
            if d == 0:
                sh.write("Query: " + query + "\n\n")
                for link in resgen: #googlesearch gen with rnum results
                    time.sleep(0.2)  #is this really necessary?? I'll leave it for now.
                    sh.write(link + "\n")
                    sh.flush()
                    links = save_results(layerpath, link, toks)   
                    for u in links:
                        URL_list.append(u)
            else: #recursive scraping
                sh.write("\n\n Layer %d: \n\n")
                layerlinks = URL_list.copy()
                URL_list = []
                for l in layerlinks:
                    sh.write(l + "\n")
                    sh.flush()
                    links = save_results(layerpath, l, toks)
                    for u in links:
                        URL_list.append(u)

#valid path from URL      
def cleanPath(url):
    filen = re.sub("/", "_", url.split("//")[1])
    filen = re.sub(r'\.', "_", filen)
    return filen
                                       
#saves wl/bl text, links, and images to proper dirs and returns list of URLs           
def save_results(savepath, URL, tokenizers):
    URLpath = os.path.join(savepath, cleanPath(URL)) #makes valid unique directory for each URL
    if not os.path.isdir(URLpath):
        os.mkdir(URLpath)
    print("Extracting Content...")
    wc, bc, urls, ims = extract_content_from_URL(URL, tokenizers)
    #URLcount += 1
    if len(URL) > 20:
        filename = URL[:20]
    else:
        filename = URL
    print("Saving Content...")
    with open(os.path.join(URLpath, "wl%s.txt"%cleanPath(filename)), "w") as wtxt: #adds whitelisted text
        for line in wc:
            wtxt.writelines(line) #do I need to iterate through the lines??
            wtxt.flush()
    with open(os.path.join(URLpath, "bl_%s.txt"%cleanPath(filename)), "w") as btxt:
        for line in bc:
            btxt.writelines(line)
            btxt.flush()
    imgcount = 0    
    for imarr in ims:
        img = Image.fromarray(imarr)
        img.save(os.path.join(URLpath, "img%d.jpg"%imgcount))
    newURLs = []
    for u in urls: #recursively appends URLs
        newURLs.append(u)
    return newURLs
                            
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

#turns url into robots.txt url
def robot_url(url):
    purl = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=purl)
    return domain + "robots.txt"

#returns list of whitelisted sentences, blacklisted sents, URLs, and images as numpy arrays
def extract_content_from_URL(URL, toks):
    links = []
    seenlink = set()
    proxy = next(get_proxies())
    try:
        r = ensure_content_length(URL, proxies={"http": proxy, "https": proxy}) #ensures the response has a Content-Length header
        try:
            req = requests.get(robot_url(URL), "HEAD")
            if req.status_code < 400:
                #parse robots.txt
                print("Robots.txt found!")
        except:
            pass
    except:
        extract_content_from_URL(URL, toks)#inefficient
    contentLen = int(r.headers["Content-Length"]) #not same as len(r.raw.read())
    for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(contentLen/1024) + 1): 
        if chunk: 
            #using bs4 whitelisting
            wtxt, wlinks, imgs = get_cont_bs(r.content)
            wsents = extract_sentences(wtxt, toks)    
            #using selectolax whitelisting
            btxt, blinks = get_cont_selectolax(r.content)
            bsents = extract_sentences(btxt, toks)
            for w in wlinks:
                if not (w in seenlink):
                    seenlink.add(w)
                    links.append(w)
            for b in blinks:
                if not (b in seenlink):
                    seenlink.add(b)
                    links.append(b)  
                  
    return wsents, bsents, links, imgs        

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
                sentcount = 0
                for sent in globals()[tok](p):
                    if not (sent in seensent) and sentcount > 3:
                        placeH = ("\nUsing extraction method #%d: " % tokcount) #displaying which tokenizer for debug purposes
                        sentences.append([placeH + sent])
                        seensent.add(sent)
                    sentcount += 1
                tokcount += 1
    return sentences            

#scrapes and returns list of proxies, default is "https://free-proxy-list.net"
def get_proxies(URL=None):
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
    return cycle(proxies)

#lets user select links and change their urls/add new ones, returning list of selected links
def select_links(links):
    URL_list = []
    for link in links:
        webbrowser.open(link, new=2)
        q = input("Include website?? Enter y/n: ")
        if re.match(q, "y"):
            print("Current URL: %s"%link)
            c = input("Do you want to change this URL?? Enter yes/no: ")
            if re.match(c, "yes"):
                url = input("Enter full new URL here: ")
                URL_list.append(url)
                moreFlag = True
                while moreFlag:
                    a = input("Would you like to enter more URLs from this site? Enter yes/no:")
                    if re.match(a, "yes"):
                        url = input("Enter new URL here: ")
                        URL_list.append(url) 
                    elif re.match(a, "no"):
                        moreFlag = False
                    else:
                        continue
            elif re.match(c, "no"):
                URL_list.append(link)
            else:
                URL_list.append(link)#catchsave?
        elif re.match(q, "n"):
            continue
        else:
            #default is not included
            continue
    return URL_list
        
#prints links/content
def read_data(stpath):      
    #goes through all links, then all content
    pass

"""FREE CODE"""
#initializing variables
cdir = os.getcwd()
storepath = os.path.join(cdir, "search") #storepath is search folder in current dir
if os.path.isdir(storepath): #clear storepath
    shutil.rmtree(storepath)
os.mkdir(storepath)
tok_list = ["extract_sentences2", "extract_sentences_smart"]
testURL = "https://en.wikipedia.org/wiki/Machine_learning"

#receive query from command line, e.g. os.system("python3 SearchBot.py quicksort -r 5 -n 15 &")
psr = argparse.ArgumentParser()
psr.add_argument("q", type=str, help="search query", metavar="query", nargs="*")
psr.add_argument("-d", type=int, help="depth of search", metavar="depth")
psr.add_argument("-n", type=int, help="number of results to search", metavar="number")
psr.add_argument("-m", type=bool, help="multiple query search", metavar="multiple")
args = psr.parse_args()
query = testURL
depth = 1
rnum = 100
mult = False
searchflag = False
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

#print("Current working directory: ", cdir,  "\n")
URLV(URLregex, query, storepath, tok_list)
if searchflag:
    if mult:
        for qry in query:
            save_search_results(search_query(qry, rnum), storepath, depth, tok_list)
    else:
        save_search_results(search_query(query, rnum), storepath, depth, tok_list)
print("\nDone.")
