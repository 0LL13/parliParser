import copy
import json
import requests

from bs4 import BeautifulSoup
from wf06_put_bsObj_in_collections import wf06_put_bsObj_in_collections



def wf07_add_nr_of_speeches():
    '''
    This is the first time that an MdL's bsObj is scraped. This function
    only looks for the number of speeches that can be found for every MdL
    at the top right corner of his speeches' overview.
    speeches_bsObj[key][url] gets another subkey ['nr_of_speeches'] and
    is saved to disk again.
    '''
    wp = wf06_put_bsObj_in_collections()
    wahlperiode = wp.wahlperiode

    for _, mdl in wp.MdLs.items():
        d = _add_nr_of_speeches(mdl)

    print('Concludes wf07 after adding the number of speeches for each MdL to wp and returning wp.')
    return wp


def _add_nr_of_speeches(mdl):
    d = mdl.speeches.collection
    if len(mdl.speeches.urls) > 1:
        for url in d:
            bsObj = d[url]['bsObj']
            #print('url', url[179:230])
            if 'like ' in bsObj[:5]:
                if 'nr_of_speeches' in d[url]:
                    pass
                else:
                    raise KeyError
            else:
                nr_of_speeches = _get_nr_of_speeches(bsObj)
                d[url]['nr_of_speeches'] = nr_of_speeches
    else:
        url = mdl.speeches.urls[0]
        try:
            bsObj = d[url]['bsObj']
            nr_of_speeches = _get_nr_of_speeches(bsObj)
            d[url]['nr_of_speeches'] = nr_of_speeches
        except KeyError as e:
            print('KeyError at ', end='')
            print(mdl.key)
            print('function _add_nr_of_speeches in wf07')
            raise

    return d


def _get_nr_of_speeches(bsObj):
    '''
    The actual scraping of the bsObj.
    Every MdL's number of speeches can be found at class "paging".
    This number is then saved.
    '''
    if bsObj == 'zero':
        nr_of_speeches = 0
    else:
        soup = BeautifulSoup(bsObj, 'lxml')

        paging = soup.find(class_ = "paging")
        if paging:
            nr_of_speeches = paging.text.split(' ')[-1]
        else:
            nr_of_speeches = 0

    return nr_of_speeches


def _test_if_mdls_got_it_right(wp):
    for _, mdl in wp.MdLs.items():
        mdl.key
        print(mdl.key)
        d = mdl.speeches.collection
        try:
            for key, value in d.items():
                print(key)
                print(value['bsObj'][:80])
                print(value['nr_of_speeches'])
            print()
        except KeyError:
            print(mdl)
            #raise


if __name__ == '__main__':
    wp = wf07_add_nr_of_speeches()
    _test_if_mdls_got_it_right(wp)
