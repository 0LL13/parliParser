# -*- coding: UTF-8 -*-

import requests
import json
from bs4 import BeautifulSoup
from scraper_data.sourceBox import headers, reden_url


def get_bsObj():
    '''
    Download bsObjs for beliebte-Vornamen.de from 1890 to 2017
    '''
    url = 'https://www.beliebte-vornamen.de/jahrgang/j{}'

    year = 1890
    for year in range (1890, 2017):
        session = requests.Session()
        URL = url.format(year)
        req = requests.get(URL, headers=headers[1])
        bsObj = BeautifulSoup(req.text, 'lxml')
        with open('./scraper_data/beliebteVornamen.soup', 'a') as fout:
            fout.write(str(bsObj))
        year += 1


def extract_names():
    with open('./scraper_data/beliebteVornamen.soup', 'r') as fin:
        bsObj = fin.read()

    nameList = list()
    for line in bsObj.split('\n'):
        if line.startswith('<a href="/') and line.endswith('</a></li>'):
            if '.htm' in line:
                name = line.split('htm">')[-1].split('</a>')[0]
                if name:
                    if len(name.split('/')) > 1:
                        for item in name.split('/'):
                            if item.replace(' ', '') not in nameList:
                                nameList.append(item.replace(' ', ''))
                    elif name not in nameList:
                        nameList.append(name.replace(' ', ''))

    sorted_nameList = sorted(nameList)
    return sorted_nameList


def get_wiki_bsObj():
    '''
    Download bsObj for germanische Vornamen as found in Wiki
    '''
    url = 'https://de.wikipedia.org/wiki/Liste_deutscher_Vornamen_germanischer_Herkunft'

    session = requests.Session()
    req = requests.get(url, headers=headers[1])
    bsObj = BeautifulSoup(req.text, 'lxml')
    with open('./scraper_data/germanischeVornamen.soup', 'w') as fout:
        fout.write(str(bsObj))


def extract_names_from_wiki_bsObj():
    with open('./scraper_data/germanischeVornamen.soup', 'r') as fin:
        bsObj = fin.read()

    nameList = list()
    for line in bsObj.split('\n'):
        if line.startswith('<li><a href="/wiki/') and \
                line.endswith('</a></li>'):
                    name = line.split('">')[-1].split('</a>')[0]
                    if '<i>' in line:
                        names = line.split('<i>')[-1]
                        while '<i>' in names:
                            name = names.split('</i>')[0]
                            if name not in nameList:
                                nameList.append(name.replace(' ', ''))
                            names = names.split('</i>')[-1]
                    elif name not in nameList:
                        nameList.append(name.replace(' ', ''))

    sorted_nameList = sorted(nameList)
    return sorted_nameList


if __name__ == '__main__':
    nameList_1 = extract_names()
    nameList_2 = extract_names_from_wiki_bsObj()
    for name in nameList_2:
        if name not in nameList_1:
            nameList_1.append(name)
    print(sorted(nameList_1))
    print(len(nameList_1))
