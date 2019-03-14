import functools
import json
import os

from bs4 import BeautifulSoup
from collections import namedtuple

from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib._extract_staedte import _make_list_of_cities
from scraper_lib._list_of_adelstitel import list_of_adelstitel
from scraper_lib._list_of_aemter import list_of_aemter
from scraper_lib._list_of_akad_titel import list_of_akad_titel
from scraper_lib._list_to_ignore import list_to_ignore
from scraper_lib._list_of_parteien import list_of_parteien
from scraper_lib._extract_vornamen import _get_vornamenListe
from scraper_lib.standardize_name import _low_cap_all
from scraper_lib._wer_regiert import _wer_regiert


def wf02_extract_wiki(legislature=None):
    """
    """

    if not legislature:
        legislature = ask_for_wahlperiode()

    bsObj = _get_bsObj(legislature)
    mdls = _collect_mdls(bsObj, legislature)

    return mdls


def _collect_mdls(bsObj, legislature):
    mdls = list()
    soup = BeautifulSoup(bsObj, 'lxml')
    for table in soup.find_all('table'):
        body = table.find('tbody')
        for rows in table.find_all('tr'):
            index = 0
            name = party = ward = None
            for cells in rows.find_all('td'):
                cell = cells.get('data-sort-value')
                if cell:
                    name = cell
                try:
                   if index == 2:
                        party = cells.contents[0].split('\n')[0]
                   elif index == 3:
                       fields = cells.text
                       fields = fields.split(' ')
                       for field in fields:
                           if _is_it_a_city(field):
                               ward = field
                               break
                except AttributeError:
                    pass
                try:
                    if legislature == '13' and name and ',' not in name:
                        next_cell = cells.find('a')
                        try:
                            if len(next_cell.contents) > 1:
                                pass
                            else:
                                if index == 0:
                                    name_13 = next_cell.contents[0]
                        except AttributeError:
                            pass
                        length = len(name)
                        last_name_13 = name_13.split(' ')[-1]
                        if len(last_name_13) < length:
                            last_name_13 = ''.join(name_13.split(' ')[-2])
                        elif len(last_name_13) > length:
                            length = len(last_name_13)
                        if 'Pieper' in name:
                            last_name_13 = 'Pieper-von Heiden'
                            length = len(last_name_13)
                        first_name_13 = name_13[:-length].strip()
                        name = last_name_13 + ', ' + first_name_13
                    elif legislature == '13' and 'Ernstmartin' in name:
                        first_name_13 = 'Ernst Martin'
                        name = last_name_13 + ', ' + first_name_13
                except TypeError:
                    pass

                if name and party and ward and index >= 3:
                    if name.split(' ')[-1] in ['van', 'von']:
                        first_name = name.split(', ')[-1]
                        first_name = first_name.split(' ')[0]
                        name = name.split(',')[0] + ', ' + first_name
                    if (name, ward, party) not in mdls:
                        mdls.append((name, ward, party))
                elif name and party and index >= 3:
                    if name.split(' ')[-1] in ['van', 'von']:
                        first_name = name.split(', ')[-1]
                        first_name = first_name.split(' ')[0]
                        name = name.split(',')[0] + ', ' + first_name
                    if (name, party) not in mdls:
                        mdls.append((name, party))
                index += 1

    return mdls

def _get_bsObj(wahlperiode):
    base = './parli_data/wf01_soup_objects/wikiListe_WP{}.soup'
    file_loc = base.format(wahlperiode)

    with open(file_loc, "r", encoding="utf-8") as fin:
        bsObj = fin.read()

    return bsObj


def _is_it_a_city(field):
    """
    Find out if the field contains the name of a city in NRW. Since this
    field is usually given when two or more MdLs share the same family name,
    this is actually the city where they got elected (Wahlkreis) and is used
    to distinguish between MdLs. From Wahlperiode 14 this will be accomplished
    by their first names.

    BAD: This function also is in wf02_extract_all_infos ...

    Returns True or False
    """

    cities = _make_list_of_cities()
    is_it_a_city = _low_cap_all(field)

    if is_it_a_city in cities:
        return True
    return False


if __name__ == "__main__":
    mdls = wf02_extract_wiki(legislature=None)
    for i, mdl in enumerate(mdls):
        print(i, mdl)
    doubles = list()
    last_names = list()
    for i, mdl in enumerate(mdls):
        #print(i+1, mdl)
        last_name = mdl[0].split(',')[0]
        if last_name not in last_names:
            last_names.append(last_name)
        else:
            doubles.append(last_name)
    print()
    #print(set(doubles))

