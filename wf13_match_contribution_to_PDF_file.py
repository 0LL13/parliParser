import copy
import dill
import os
import sys

from collections import namedtuple
from collections import defaultdict
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib.standardize_name import _low_cap_all


def wf13_match_contribution_to_PDF_file():
    legislature = ask_for_wahlperiode()
    dir_loc = f'./parli_data/wf11_sessions/WP{legislature}/'
    url_base = 'https://www.landtag.nrw.de/portal/WWW/dokumentenarchiv/Dokument?Id='
    if os.path.isdir(dir_loc):
        print(dir_loc)
    wp = _open_dilled_wp(legislature)

    print(f'{wp.number_of_MdLs} parliamentarians in legislature {wp.wahlperiode}.')

    for _, mdl in wp.MdLs.items():
        contributions = copy.deepcopy(mdl.contributions)
        #print(mdl.key)
        for protocol_nr, contribution in contributions.items():
            _match_to_file(wp, mdl, protocol_nr, contribution)

    #for _, mdl in wp.MdLs.items():
    #    print(mdl.key)
    #    for protocol_nr, contribution in mdl.contributions.items():
    #        print(protocol_nr)
    #        print(contribution)
    #    print()

    dir_loc = f'./parli_data/wf13_contributions/'
    os.makedirs(dir_loc, exist_ok=True)

    file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
    with open(file_loc, 'wb') as fout:
        dill.dump(wp, fout)


def _match_to_file(wp, mdl, protocol_nr, contribution):
    #print(protocol_nr)
    #print(contribution)
    #lost_contributions = dict()
    #lost_contributions[mdl.key] = dict()
    for start_end, contri in contribution.items():
        #print(start_end, contri)
        start = int(start_end[0])
        end = int(start_end[-1])
        for key, session in wp.sessions.items():
            if protocol_nr == key.protocol_nr:
                if '&' in session.url:
                    urls = session.url.split('&')
                    for url in urls:
                        c = _find_url(start, end, url)
                        if c != None:
                            d = mdl.contributions[protocol_nr][start_end]
                            d['url'] = c
                        else:
                            pass    # not sure how to handle this
                else:
                    url = session.url
                    c = _find_url(start, end, url)
                    if c != None:
                        d = mdl.contributions[protocol_nr][start_end]
                        d['url'] = c
                    else:
                        pass    # not sure how to handle this

    #return lost_contributions


def _find_url(start, end, url):
    page_delimiters = url.split('|')
    beginning = int(page_delimiters[-2])
    ending = int(page_delimiters[-1])
    c = None
    if start == beginning and end <= ending:
        c = url.split('Id=')[-1]
    elif start >= beginning and end == ending:
        c = url.split('Id=')[-1]
    elif start >= beginning and end <= ending:
        c = url.split('Id=')[-1]
    elif start < beginning and end == ending:
        c = None

    return c


def _open_dilled_wp(legislature):
    '''
    '''
    dir_loc = f'./parli_data/wf12_contributions/'
    file_loc = dir_loc + 'WP_{}.dill'.format(legislature)

    with open(file_loc, 'rb') as fin:
        wp = dill.load(fin)

    return wp


if __name__ == '__main__':
    wf13_match_contribution_to_PDF_file()

