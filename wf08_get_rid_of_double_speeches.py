import json
import os
import sys

from bs4 import BeautifulSoup

from wf07_scraping_bsObj_for_nr_of_speeches import wf07_add_nr_of_speeches


def wf08_get_rid_of_double_speeches(wahlperiode=False):
    '''
    Check if a url points to a non-existent HTML site. In this case there will
    be zero speeches --> rename bsObj to "zero"
    Check if two urls point to the same collection of speeches (same amount
    of speeches), in this case rename one url with "like other url"

    Reminder: d = mdl.speeches.collection (dict)
    '''

    wp = wf07_add_nr_of_speeches()
    wahlperiode = wp.wahlperiode

    for _, mdl in wp.MdLs.items():
        key = mdl.key
        d = mdl.speeches.collection
        if len(mdl.speeches.urls) > 1:
            compare = dict()
            for url in d:
                d = _get_rid_of_bsObjs_with_zero_speeches(d, url, key)
                compare = _collect_urls_to_compare(d, url, compare)
            if len(compare) > 1:
                d = _get_rid_of_urls_with_same_speeches(d, compare)
        else:
            url = mdl.speeches.urls[0]
            d = _get_rid_of_bsObjs_with_zero_speeches(d, url, key)

    speeches_bsObj = dict()
    for key, value in wp.MdLs.items():
        speeches_bsObj[key] = value.speeches.collection

    dir_loc = './parli_data/wf08_speeches_bsObj/'
    if os.path.isdir(dir_loc):
        pass
    else:
        os.mkdir(dir_loc)

    file_loc = dir_loc + 'WP_{}_speeches_bsObj.dict'.format(wahlperiode)

    if __name__ == '__main__':
        if os.path.exists(file_loc):
            check = input("File exists, overwrite? y/n")
            if check == "y":
                with open(file_loc, 'w', encoding='utf-8') as fout:
                    json.dump(speeches_bsObj, fout)
            else:
                print('No download')

    print('Concludes wf08 after getting rid of double entries for the same url pointing to the speeches of an MdL and returns wp.')

    return wp


def _test_if_mdls_got_it_right(wp):
    for _, mdl in wp.MdLs.items():
        mdl.key
        print(mdl.key)
        d = mdl.speeches.collection
        l = len(d)
        counter = 0
        for key, value in d.items():
            print(f'url:\n{key}')
            print(f'bsObj:\n{value["bsObj"][:75]}')
            print(f'nr_of_speeches:\n{value["nr_of_speeches"]}')
            counter += 1
            if counter < l:
                print('-'*20)
        print()


def _get_rid_of_bsObjs_with_zero_speeches(d, url, key):
    try:
        bsObj = d[url]['bsObj']
        nr_of_speeches = d[url]['nr_of_speeches']
        if bsObj[:5] != 'like ':
            if nr_of_speeches == 0:
                d[url]['bsObj'] = 'zero'
    except KeyError as e:
        print('KeyError at ', end='')
        print(key)
        print('function _get_rid_of_bsObjs_with_zero_speeches in wf08')
        raise

    return d


def _collect_urls_to_compare(d, url, compare):
    bsObj = d[url]['bsObj']
    if bsObj == 'zero':
        pass
    else:
        nr_of_speeches = d[url]['nr_of_speeches']
        compare[url] = nr_of_speeches

    return compare


def _get_rid_of_urls_with_same_speeches(d, compare):
    for u_r_l in compare:
        if d[u_r_l]['bsObj'][:5] == 'like ':
            continue
        else:
            nr = compare[u_r_l]
            if _same_nr_of_speeches(d, u_r_l, nr):
                url = _url_with_same_nr_of_speeches(d, u_r_l, nr)
                if d[url]['bsObj'][:5] == 'like ':
                    pass
                else:
                    bs_obj = u_r_l[179:]
                    bs_obj = bs_obj.split('%27%27%29+and+%28')[0]
                    d[url]['bsObj'] = 'like {}'.format(bs_obj)

    return d


def _same_nr_of_speeches(d, u_r_l, nr):
    for url in d:
        if url != u_r_l:
            nr_of_speeches = d[url]['nr_of_speeches']
            if nr_of_speeches == nr:
                return True
    return False


def _url_with_same_nr_of_speeches(d, u_r_l, nr):
    for url in d:
        if url != u_r_l:
            nr_of_speeches = d[url]['nr_of_speeches']
            if nr_of_speeches == nr:
                return url


if __name__ == '__main__':
    wp = wf08_get_rid_of_double_speeches()
    _test_if_mdls_got_it_right(wp)
