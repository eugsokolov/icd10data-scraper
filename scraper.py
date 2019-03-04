from __future__ import print_function
import grequests
import requests
from bs4 import BeautifulSoup
from multiprocessing import Pool
from main import ICDCode, RangedSite

SITE = 'https://www.icd10data.com'
CODES = '{}/ICD10CM/Codes/'.format(SITE)


def yieldParentSites():
    resp = requests.get(CODES)
    soup = BeautifulSoup(resp.content, 'html.parser')
    for div in soup.find_all('ul', class_='ulPopover'):
        for child in div.find_all('a'):
            yield SITE + child['href']

class Downloader():
    def __init__(self, sites):
        self.sites = sites

    def exception(self, request, exception):
            print("error: {} {}".format(request.url, exception))

    def run(self):
        return grequests.imap(
            (grequests.get(u) for u in self.sites),
            exception_handler=self.exception,
            size=5)

class Parser():
    def __init__(self, response):
        self.response = response
        self.content = response.content
        self.soups = []

    def yieldLinks(self, soup):
        for div in soup.find_all('ul', class_='ulPopover'):
            for child in div.find_all('a'):
                yield SITE + child['href']

    def runParent(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        return self.yieldLinks(soup)

    @property
    def code(self):
        return self.parseCode(self.response.url)

    @classmethod
    def parseCode(cls, url):
        return url.split('/')[-1]

    def getSynonyms(self, soup):
        span = soup.find(text='Approximate Synonyms')
        if not span:
            return
        table = span.parent.next_element.next_element.next_element
        return [i.text for i in table.find_all('li')]

    def runChild(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        synonyms = self.getSynonyms(soup)
        if synonyms:
            return self.code, synonyms

class Scraper():
    def mapChild(self, content):
        p = Parser(content)
        return p.runChild()

    def runForSites(self):
        d = Downloader(yieldParentSites())
        for parent in d.run():
            p = Parser(parent)
            children = Downloader(p.runParent())
            yield children

    def runForSynonyms(self):
        d = Downloader(yieldParentSites())
        for parent in d.run():
            p = Parser(parent)
            children = Downloader(p.runParent())
            with Pool(10) as p:
                out = p.map(self.mapChild, children.run())
                print('parsed', len(out), 'pages for site', parent.url)
                yield out

def loadAllCodes():
    # todo make this non blocking
    s = Scraper()
    print('running scraper')
    for items in s.runForSynonyms():
        # todo: bulk save items because this is ridiculous
        count = 0
        for item in items:
            if item:
                code, synonyms = item
                ICDCode(code=code, synonyms=synonyms).save()
                count += 1
        print('saved', count, 'items to the database')

if __name__ == '__main__':
    loadAllCodes()

def fillRangedSites():
    s = Scraper()
    for site in s.runForSites():
        start, end = site.split('/')[-1].split('-')
        RangedSite(site=site, start=start, end=end).save()

def findRangedSite(code):
    if not RangedSite.query.count():
        fillRangedSites()
    for site in RangedSite.query:
        # todo improve this querying/filtering
        start, end = site.start, site.end
        if code[0] in {start[0], end[0]}:
            if int(start[1:]) <= int(code[1:3]) <= int(end[1:]):
                return site.site
    raise ValueError('unable to find range site for {}'.format(code))

def getFromSite(code):
    d = Downloader([findRangedSite(code)])
    p = Parser(next(d.run()))
    for site in p.runParent():
        if code == Parser.parseCode(site):
            d = Downloader([site])
            try:
                code, synonyms = Parser(next(d.run())).runChild()
            except TypeError:
                return # error with response
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

def load():
    # todo: make this work via post request
    #loadAllCodes()
    return 'must run load manually'

