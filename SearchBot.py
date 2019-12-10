##SearchBot e.g. SearchBot.py www.youtube.com or SearchBot.py engineering -r 5 -n 50
#A program to facilitate research, meaning Google search + web scraping + content compilation + LP summarization
# TODO:
# receive query from command line
# check query for URL and prompt navigation
# print first 50 Google Search result URLs
# make priority queue with value function using content similarity to corpus
# use top 20% of url's content to 

#pip install bs4, requests, scholarly, html5lib, google, progressbar2, clint, etc.
import sys, os, time, progressbar
import re #URL Validation
import bs4 #web scraper
import argparse #command line arguments
import requests #HTTP request
import scholarly #Google Scholar search
import webbrowser #open URL in browser
from googlesearch import search #Google Search results list
from clint.textui import progress #download progress bar

#receive query from command line
psr = argparse.ArgumentParser()
psr.add_argument("q", type=str, help="search query", metavar="query", nargs="*")
psr.add_argument("-r", dest="refinement", type=int, help="number of results per page, refinement factor", metavar="refinement")
psr.add_argument("-n", type=int, help="number of results to search", metavar="number")
args = psr.parse_args()
query = str(args.q)
rnum = 15
snum = 1000
if args.refinement is not None:
    rnum = int(args.refinement)
if args.n is not None:
    snum = int(args.n)

#URL Validation Regular Expression
URLregex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

print("\nYour search query is a website:", re.match(URLregex, query) is not None)
#Direct URL Prompt
def URLQ(regex, qry):
    if re.match(regex, qry) is not None:
        q = input("Do you want to go straight to the URL?? Enter yes/no: ")
        if re.match(q, "yes"):
            webbrowser.open(qry)
        elif re.match(q, "no"):
            pass
        else:
            URLQ(regex, qry)
URLQ(URLregex, query)

#variable number of search results and results per page
results = search(query, num=rnum, pause=1.77, stop=snum)

count = 0
storepath = "C:/Users/vivim/OneDrive/Desktop/MiscCode/search.txt"
contentpath = "C:/Users/vivim/OneDrive/Desktop/MiscCode/content.txt"
"""
if os.path.isdir(storepath) is False:
os.mkdir(storepath)
"""
with open(storepath,"wb") as sh:
    for link in results:
        time.sleep(0.2)
        ''' supposed to be a stable progress bar
        if snum is not None:
            print('Search progress: [%d%%]\r'%(count/snum*100))
            #print('Search progress: [%d%%]\r'%(count/snum*100))
        else:
            print('Search progress: [%d%%]\r'%(count/10))
            #print('Search progress: [%d%%]\r'%(count/10))
        '''    
        sh.writelines(link)
        #print(link)
        sh.flush()
        r = requests.get(URL, stream=True)
        total_length = int(r.headers.get('content-length'))
        for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length/1024) + 1): 
            if chunk:
                with open(contentpath,"wb") as cp:
                    cp.write(chunk)
                    cp.write(r.content)
                    cp.flush()
                    
        count += 1
        
with open(storepath, "r") as hreader:
    for line in hreader:
        print(line)

with open(contentpath, "r") as creader:
    for line in creader:
        print(line)
        
os.system("python3 SearchBot.py coding -r 10 -n 100")
