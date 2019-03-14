import json
import os
import random
import reprlib
import sys

from wf00_base_classes import Wahlperiode
from wf00_base_classes import MdL
from wf02_extract_all_infos_about_MdLs import wf02_extract_all_infos_about_MdLs
from wf02_extract_all_infos_about_MdLs import _count_total_number_of_lines
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib._wer_regiert import _wer_regiert


def wf03_mk_top_container_wahlperiode(wahlperiode=None):
    """
    Creates a class Wahlperiode container that has all the informations that
    could be extracted from the bsObj.
    Create a key from these informations that will be unique for each
    parlamentarian.
    Key looks like this:
        lastname_firstname_electoralward_legislature
    If there is no electoral ward available, "ew" will placehold instead.

    Returns wp
    """

    if not wahlperiode:
        wahlperiode = ask_for_wahlperiode()
    wp = Wahlperiode(int(wahlperiode))

    mdls = wf02_extract_all_infos_about_MdLs(wahlperiode)
    total = len(mdls)
    counter = 0
    for _, mdl_ in mdls.items():
        key_ = mdl_.key
        key = '{}_{}_{}_{}'.format(mdl_.last_name, mdl_.first_name,\
                mdl_.electoral_ward, mdl_.legislature)
        if key != key_:
            raise Exception('wf03 needs attention')
        if key not in wp.MdLs:
            wp.MdLs[key] = mdl_
            counter += 1
        else:
            mdl = wp.MdLs[key]
            mdl = _append_to_dict_entry(key, mdl, mdl_)
            wp.MdLs[key] = mdl
            total -= 1
            print('total', total)

    print('{} of {} MdLs'.format(counter, total))
    if counter != total:
        raise Exception("The number of MdLs and the number of names are not equal.")

    wp.number_of_MdLs = counter
    names = list(set(wp.names))
    names = _bubblesort(names)
    wp.names = names
    print('Concludes wf03 by returning wp.names')

    return wp


def _bubblesort(names):
    names_to_sort = names
    for iter_num in range(len(names)-1, 0, -1):
        for idx in range(iter_num):
            try:
                if names[idx][0] > names[idx+1][0]:
                    temp = names[idx]
                    names[idx] = names[idx+1]
                    names[idx+1] = temp
            except TypeError:
                print(type(names))
                raise

    return names


def _append_to_dict_entry(key, mdl, mdl_):
    for office in mdl_.office:
        if office not in mdl.office:
            mdl.office.append(office)
    for party in mdl_.party:
        if party not in mdl.party:
            mdl.party.append(party)
    if not mdl.peer_title:
        mdl.peer_title = mdl_.peer_title
    if not mdl.academic_title:
        mdl.academic_title = mdl_.academic_title
    if not mdl.parl_pres:
        mdl.parl_pres = mdl_.parl_pres

    return mdl


def _id():
    '''
    Make an ID of type str that consists of four numbers/letters (a-z, A-Z, 0-9).
    Number of combinations will be 52*62^3 = 12.393.056 (repetition being allowed,\
    the first position will be in a-z or A-Z).
    This ID number will be used for parlamentarians and speeches alike.
    If there are 220 parlamentarians for each period and each will give about 75
    speeches then 10 periods will need 165.000 IDs plus about 2.200 IDs for the
    MdLs.

    Returns an ID like 'ya3T', 'RF8s', 'a60w', 'Sbb4', ...
    '''

    ascii_lowercase = 'abcdefghijklmnopqrstuvwxyz'
    ascii_uppercase = 'ABCDEFGHIJKLMNOPQRSSTUVWXYZ'
    digits = '0123456789'

    file_loc = './parli_data/id_numbers.txt'
    if os.path.isfile(file_loc):
        with open(file_loc, 'r', encoding='utf-8') as fin:
            ids = json.load(fin)
    else:
        ids = list()

    pick_first = ascii_lowercase + ascii_uppercase
    pick = ascii_lowercase + ascii_uppercase + digits

    id_nr = random.choice(pick_first)
    id_nr = id_nr + random.choice(pick) + random.choice(pick) + random.choice(pick)

    ids.append(id_nr)

    with open(file_loc, 'w', encoding='utf-8') as fout:
        json.dump(ids, fout)

    return id_nr


if __name__ == "__main__":
    print(sys.version)
    wp = wf03_mk_top_container_wahlperiode()
    mdls = wp.MdLs
    for key, mdl in mdls.items():
        if mdl.office:
            print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}, {mdl.office}')
            print(f'{mdl.line}')
            print()
        elif mdl.parl_pres:
            print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}, {mdl.parl_pres}')
            print(f'{mdl.line}')
            print()
        #print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}')
        #if len(mdl.party) > 1:
        #    print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}, {mdl.office}')

    #for name in wp.names:
    #    print(name)
