import copy
import json
import requests

from bs4 import BeautifulSoup
from wf00_base_classes import Speeches
from wf03_mk_top_container_wahlperiode import wf03_mk_top_container_wahlperiode
from wf04_add_search_urls_to_wp import wf04_add_search_urls_to_wp


def wf06_put_bsObj_in_collections():
    '''
    speeches = Speeches()
    wahlperiode = mdl.wahlperiode
    urls = list()
    collection = dict()
    all_speeches = speeches.Speeches(urls, collection)
    mdl.speeches = speeches
    '''

    wp = wf03_mk_top_container_wahlperiode()
    wp = wf04_add_search_urls_to_wp(wp)
    wahlperiode = wp.wahlperiode

    dir_loc = './parli_data/wf05_speeches_bsObj/'
    file_loc = dir_loc + 'WP_{}_speeches_bsObj.dict'.format(wahlperiode)
    with open(file_loc, 'r', encoding='utf-8') as fin:
        speeches_bsObj = json.load(fin)
    print('json.load of speeches_bsObj, as downloaded and saved in wf05.')

    for _, mdl in wp.MdLs.items():
        key = mdl.key
        d = mdl.speeches.collection
        if key in speeches_bsObj:
            for url, bsObj in speeches_bsObj[key].items():
                try:
                    if d[url]['bsObj'] == bsObj:
                        pass
                except KeyError:
                    d[url] = dict()
                    d[url]['bsObj'] = bsObj
                    #print(url[:70])
                    #print(d[url]['bsObj'][:70])
        else:
            print(key)
            print(mdl.speeches.collection)
            break

    print('Concludes wf06 and returns wp after putting the bsObjs into the mdl.speeches.collection.')
    return wp


def _test_if_mdls_got_it_right(wp):
    for _, mdl in wp.MdLs.items():
        mdl.key
        print(mdl.key)
        d = mdl.speeches.collection
        for key, value in d.items():
            print(key)
            print(value['bsObj'][:70])
        print()


if __name__ == '__main__':
    wp = wf06_put_bsObj_in_collections()
    _test_if_mdls_got_it_right(wp)
