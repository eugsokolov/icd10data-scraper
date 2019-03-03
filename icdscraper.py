from __future__ import print_function
import grequests
import requests
import threading
from bs4 import BeautifulSoup
from main import ICDCode, RangedSite

SITE = 'https://www.icd10data.com'
SEARCH = '{}/search?s='.format(SITE)
CODES = '{}/ICD10CM/Codes/'.format(SITE)

import resource
resource.setrlimit(resource.RLIMIT_NOFILE, (110000, 110000))

class Parser():
    # todo: add better support for scraping all ICD codes
    def __init__(self):
        pass

    def exception(self, request, exception):
        print("error: {} {}".format(request.url, exception))

    def getContent(self, path):
        return requests.get(path)

    def getSoup(self, path):
        page = self.getContent(path)
        return BeautifulSoup(page.content, 'html.parser')

    def yieldLinks(self, soup):
        for div in soup.find_all('ul', class_='ulPopover'):
            for child in div.find_all('a'):
                yield SITE + child['href']

    def getAllParentPaths(self):
        return self.yieldLinks(self.getSoup(CODES))

    def getAllParentContents(self):
        results = grequests.imap(
            (grequests.get(u) for u in self.getAllParentPaths()),
            exception_handler=self.exception,
            size=5)
        return results

    def getAllChildrenSites(self, content):
        return self.yieldLinks(BeautifulSoup(content, 'html.parser'))

    def getAllChildrenResponses(self, content):
        # todo: speed up via multithreading?
        responses = grequests.imap(
            (grequests.get(u) for u in self.getAllChildrenSites(content)),
            exception_handler=self.exception,
            size=7)
        return responses

    def getSynonyms(self, soup):
        span = soup.find(text='Approximate Synonyms')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element
        return [i.text for i in table.find_all('li')]

    def getCodeFromURL(self, url):
        return url.split('/')[-1]

    def parseChildResponse(self, response):
        if not response:
            return # error with response
        code = self.getCodeFromURL(response.url)
        soup = BeautifulSoup(response.content, 'html.parser')
        synonyms = self.getSynonyms(soup)
        if synonyms:
            ICDCode(code=code, synonyms=synonyms).save()

    def scrape(self):
        for parentResponse in self.getAllParentContents():
            responses = self.getAllChildrenResponses(parentResponse.content)
            # todo: speed up with multiprocessing?
            for response in responses:
                self.parseChildResponse(response)

def loadCodes():
    p = Parser()
    thread = threading.Thread(target=p.scrape())
    thread.start() #  we don't want this to block other requests
    return ICDCode.query.count()

def fillRanged():
    p = Parser()
    for site in p.getAllParentPaths():
        start, end = site.split('/')[-1].split('-')
        RangedSite(site=site, start=start, end=end).save()

def findRangedSite(code):
    if not RangedSite.query.count():
        fillRanged()
    for site in RangedSite.query:
        # todo improve this querying/filtering
        start, end = site.start, site.end
        if code[0] in {start[0], end[0]}:
            if int(start[1:]) <= int(code[1:3]) <= int(end[1:]):
                return site.site
    raise ValueError('unable to find range site for {}'.format(code))

def getFromSite(code):
    p = Parser()
    page = p.getContent(findRangedSite(code))
    for site in p.getAllChildrenSites(page.content):
        if code == p.getCodeFromURL(site):
            synonyms = p.getSynonyms(p.getSoup(site))
            if synonyms:
                ICDCode(code=code, synonyms=synonyms).save()
                print('found {} synonyms online, cached it'.format(code))
                return synonyms

def getFromDatabase(code):
    data = ICDCode.query.filter(ICDCode.code == code).first()
    if data:
        print('found {} synonyms in db'.format(code))
        return data.synonyms

def cleanCode(code):
    # https://www.stata.com/manuals/dicd10.pdf
    from re import match
    if (match(r'^[A-Z][0-9]{2}$', code) or
            match(r'^[A-Z][0-9]{2}\.[0-9]{1,3}$', code)):
        return code
    if match(r'^[A-Z][0-9]{2}[0-9]{1,3}$', code):
        return code[0:3] + '.' + code[3:]
    raise ValueError('Bad code regex given for {}'.format(code))

def get(code):
    code = cleanCode(code)
    synonyms = getFromDatabase(code) or getFromSite(code)
    return synonyms

