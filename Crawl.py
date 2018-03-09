"""Simple Crawler

Usage:
    Crawl.py -s <startpage> -m <maxpages>



Options:
  -h, --help     Show this screen.
  -s, --startpage <startpage>   URL to begin Crawl, default is http://python.org
  -m, --maxpages <maxpages>     Maximum pages to crawl, default is 100

"""

import collections

from timeit import default_timer
from urllib.parse import urldefrag, urljoin, urlparse

import bs4
from docopt import docopt
import requests

#------------------------------------------------------------------------------
def crawler(startpage='http://python.org', maxpages=100):

    pagequeue = collections.deque() # queue of pages to be crawled
    pagequeue.append(startpage)
    crawled = [] # list of pages already crawled
    domain = urlparse(startpage).netloc

    pages = 0 # number of pages succesfully crawled so far
    failed = 0 # number of links that couldn't be crawled

    sess = requests.session() # initialize the session
    while pages < maxpages and pagequeue:
        url = pagequeue.popleft() # get next page to crawl (FIFO queue)
        if ( url.startswith("//") ):
            url = "http:" + url

        # read the page
        try:
            response = sess.get(url)
        except (requests.exceptions.MissingSchema,
                requests.exceptions.InvalidSchema):
            print("*FAILED*:", url)
            failed += 1
            continue
        if not response.headers['content-type'].startswith('text/html'):
            continue # don't crawl non-HTML content

        # Note that we create the Beautiful Soup object here (once) and pass it
        # to the other functions that need to use it
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        # process the page
        crawled.append(url)
        pages += 1
        if pagehandler(url, response):
            # get the links from this page and add them to the crawler queue
            links = getlinks(url, domain, soup)
            for link in links:
                if not url_in_list(link, crawled) and not url_in_list(link, pagequeue):
                    pagequeue.append(link)

    print('{0} pages crawled, {1} links failed.'.format(pages, failed))

#------------------------------------------------------------------------------
def getlinks(pageurl, domain, soup):
    '''
    Gets the links within the page
    :param pageurl:
    :param domain:
    :param soup:
    :return:
    '''
    # get target URLs for all links on the page
    links = [a.attrs.get('href') for a in soup.select('a[href]')]

    # remove fragment identifiers
    links = [urldefrag(link)[0] for link in links]

    # remove any empty strings
    links = [link for link in links if link]

    # if it's a relative link, change to absolute
    links = [link if bool(urlparse(link).netloc) else urljoin(pageurl, link) \
        for link in links]

    # if only crawing a single domain, remove links to other domains
    if domain:
        links = [link for link in links if samedomain(urlparse(link).netloc, domain)]

    return links

#------------------------------------------------------------------------------
def pagehandler(pageurl, pageresponse):

    print('Crawling:' + pageurl + ' ({0} bytes)'.format(len(pageresponse.text)))
    return True

#------------------------------------------------------------------------------
def samedomain(netloc1, netloc2):
    '''
    This method makes sure we stay within the start page's domain by comparing the url.
    google.com == drive.google.com== mail.google.com == True
    this functiion ensures we stay within google.com and any sub domain is irrelevent
    :param netloc1:
    :param netloc2:
    :return:
    '''
    domain1 = netloc1.lower()
    if '.' in domain1:
        domain1 = domain1.split('.')[-2] + '.' + domain1.split('.')[-1]

    domain2 = netloc2.lower()
    if '.' in domain2:
        domain2 = domain2.split('.')[-2] + '.' + domain2.split('.')[-1]

    return domain1 == domain2

#------------------------------------------------------------------------------
def url_in_list(url, listobj):
    '''
        since both the https and https links have the same content it would be enough if we crawl either so this function
        avoid re-crawling of a page
    :param url:
    :param listobj:
    :return:
    '''
    http_version = url.replace('https://', 'http://')
    https_version = url.replace('http://', 'https://')
    return (http_version in listobj) or (https_version in listobj)

#------------------------------------------------------------------------------

if __name__ == "__main__":
    arguments = docopt(__doc__)
    START = default_timer()
    crawler(arguments['--startpage'], maxpages=int(arguments['--maxpages']))
    END = default_timer()
    print('Elapsed time (seconds) = ' + str(END-START))