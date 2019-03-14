import copy
import json
import os
import requests
import sys

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from pprint import pprint
from bs4 import BeautifulSoup
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from wf03_mk_top_container_wahlperiode import wf03_mk_top_container_wahlperiode
from wf04_add_search_urls_to_wp import wf04_add_search_urls_to_wp


def requests_retry_session(
        retries=3,
        backoff_factor=0.8,
        status_forcelist=(500, 502, 504),
        session=None,
        headers=None,
        ):
    '''
    https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    Setup to retry a url a sensible number of times and quit knowing why it
    didn't work.
    '''
    session = session or requests.Session()
    retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def wf05_get_speech_bsObj():
    '''
    Function wf05_get_speech_bsObj will download the bsObj from the Landtag
    site which contains all links to speeches held by that particular MdL.

    Dictionaries called "speeches" will look like this:
        {MdL-key: {url_1: bsObj_1, url_2: bsObj_2, ...}} depending on how
        many urls are available (usually just one)

    To this end WP_{}_speeches_bsObj.dict is opened and json-loaded.

    For every MdL-key I check if it has any urls pointing to the bsObj.
    If not, an empty list is created so as to avoid a future KeyError.
    The urls that had been previously (wf04) created are used to request the
    bsObj to be found under that url. This bsObj is then saved using the url as
    the key for that bsObj. An error will be saved in the same way for the url
    that caused the error.
    An existing WP_{}_speeches_bsObj.dict is being updated on the go.
    Finally speeches_bsObj is json-dumped again to save it.

    Returns nothing.
    '''

    dir_loc = './parli_data/wf05_speeches_bsObj/'
    if os.path.isdir(dir_loc):
        pass
    else:
        os.mkdir(dir_loc)

    wp = wf03_mk_top_container_wahlperiode()
    wp = wf04_add_search_urls_to_wp(wp)
    wahlperiode = wp.wahlperiode

    file_loc = dir_loc + 'WP_{}_speeches_bsObj.dict'.format(wahlperiode)
    if os.path.isfile(file_loc):
        with open(file_loc, 'r', encoding='utf-8') as fin:
            speeches_bsObj = json.load(fin)
    else:
        speeches_bsObj = dict()

    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                             AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
               "Accept":"html,application/xhtml+xml,application/xml;\
                         q=0.9,image/webp,*/*;q=0.8"}

    speeches_bsObj = _change_keys(speeches_bsObj)

    for _, mdl in wp.MdLs.items():
        key = mdl.key
        if key in speeches_bsObj:
            for url in mdl.speeches.urls:
                if url in speeches_bsObj[key]:
                    print('.', end='')
                else:
                    print('*', end='')
                    bsObj = _do_the_actual_download_of_the_bsObj(url, headers)
                    speeches_bsObj[key][url] = bsObj
        else:
            print('Key not in dict yet', key)
            speeches_bsObj[key] = dict()
            for url in mdl.speeches.urls:
                search_key = url.split('name+phrase+like+%27%27')[-1]
                search_key = search_key.split('%27%27%29+and')[0]
                print('Downloading', search_key)
                bsObj = _do_the_actual_download_of_the_bsObj(url, headers)
                speeches_bsObj[key][url] = bsObj

    with open(file_loc, 'w', encoding='utf-8') as fout:
        json.dump(speeches_bsObj, fout)

    print()
    print('This concludes wf05, download of all bsObjs concerning speeches.')


def _do_the_actual_download_of_the_bsObj(url, headers):
    try:
        session = requests_retry_session()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        bsObj = BeautifulSoup(response.content, 'lxml')
    except requests.exceptions.HTTPError as err:
        print(err.arg[0])
    except requests.exceptions.Timeout as err:
        print(err.arg[0])
    except requests.exceptions.RetryError as e:
        print('Retry error at {}'.format(url))
        print(e)
        bsObj = e
        sys.exit(1)

    return str(bsObj)


def _change_keys(speeches_bsObj):
    speeches = copy.deepcopy(speeches_bsObj)
    for key in speeches_bsObj:
        if 'vN' in key:
            if 'wk' in key:
                name = key.split('_')[0]
                leg = key.split('_')[-1]
                new_key = '{}_{}_{}_{}'.format(name, 'fn', 'ew', leg)
                speeches[new_key] = speeches_bsObj[key]
                del speeches[key]
            else:
                name = key.split('_')[0]
                ward = key.split('_')[-2]
                leg = key.split('_')[-1]
                new_key = '{}_{}_{}_{}'.format(name, 'fn', ward, leg)
                speeches[new_key] = speeches[key]
                del speeches[key]
        elif 'wk' in key:
            name = key.split('_')[0]
            first_name = key.split('_')[1]
            leg = key.split('_')[-1]
            new_key = '{}_{}_{}_{}'.format(name, first_name, 'ew', leg)
            speeches[new_key] = speeches_bsObj[key]
            del speeches[key]

    return speeches


if __name__ == '__main__':
    wf05_get_speech_bsObj()
