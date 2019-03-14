import functools
import json
import os
import sys

from bs4 import BeautifulSoup

from wf00_base_classes import Wahlperiode
from wf00_base_classes import MdL
from wf00_base_classes import NameNotFoundError
from wf022_extract_wiki import wf02_extract_wiki

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


def wf02_extract_all_infos_about_MdLs(legislature=None, verbose=False):
    """
    Extracting the bsObj for all available infos about MdLs and legislature.
    Necessary to create a key and a dict later.

    Informations:   last name
                    first name
                    electoral ward
                    party
                    office
                    peer title
                    academic title
                    parliament president
                    legislature

    If there is no first name available, "fn" will placehold instead.
    Yields a named tuple with all variables called 'mdl' with name of
    elctoral ward or 'ew' if none, also with first name or 'fn' if none.
    Otherwise as defined in wf00_base_classes, class "MdL", either an
    empty list or "False".
    Additionally yields legislature and line that contains those information
    for later checking.

    Returns dict "mdls"
    """

    if not legislature:
        leg = ask_for_wahlperiode()     # wahlperiode: legislature
    else:
        leg = legislature

    wp = Wahlperiode(int(leg))
    bsObj = _get_bsObj(leg)
    mdls = _collect_mdls(bsObj, wp, leg, verbose)
    print('Concludes wf02 with returning mdls (a dictionary with all MdLs of a legislature).')

    return mdls


def _collect_mdls(bsObj, wp, leg, verbose):
    mdls = dict()
    if int(leg) < 14:
        mdls_wiki = wf02_extract_wiki(leg)
    else:
        mdls_wiki = None
    for line in bsObj.split("\n"):
        if line.startswith("<option ") and line.endswith("</option>"):
            fields = line.split('value="')[1].split('">')[0][1:-1]
            fields_academic = line.split('">')[-1].split("</")[0]
            field_list = _make_list_of_fields(fields)

            # last_name can make use of the comma from legislature >= 14
            # fields still got that comma
            last_name = _get_last_name(fields, wp)
            if not last_name:
                raise NameNotFoundError
                #continue
            wp.last_names.append(last_name)

            # now continue with items seperated by ' '
            if len(field_list) == 1:
                # stuff like 'DATENBEAUFTRAGTER'
                continue
            first_name = _get_first_name(field_list, last_name, wp)
            electoral_ward = _get_wahlkreis(field_list)
            party = _get_partei(field_list)
            party =  _find_missing_party(party, leg, last_name)
            office = _get_amt(field_list, wp)
            peer_title = _get_adelstitel(fields_academic, last_name)
            academic_title = _get_akad_titel(fields_academic, last_name)
            parl_pres = _get_parl_pres(field_list)
            if int(leg) < 14:
                first_name = _align_with_wiki(leg, last_name, first_name, party,\
                        electoral_ward, mdls_wiki, line)

            # Protocols before leg 14 will identify MdL with last_name and
            # electoral ward, from leg 14 on with last_name and first_name.
            # Because of this I chose electoral_ward over first_name to add
            # in wp.names. From leg 14 there will not be any electoral wards
            # anyway.
            if electoral_ward != 'ew':
                wp.wards.append(electoral_ward)
                wp.names.append((last_name, electoral_ward))
            elif first_name != 'fn':
                wp.first_names.append(first_name)
                wp.names.append((last_name, first_name))
            else:
                wp.names.append((last_name, ))
            new_mdl = _mk_new_MdL(leg, last_name, first_name, electoral_ward,\
                    party, office, peer_title, academic_title, parl_pres, line)
            res, old_key = _check_new_mdl(mdls, new_mdl)
            mdls = _add_or_change_mdls(res, old_key, mdls, new_mdl)
            if verbose:
                if office:
                    print(new_mdl)
                elif parl_pres:
                    print(new_mdl)

    return mdls


def _add_or_change_mdls(res, old_key, mdls, new_mdl):
    if res == 'new':
        mdls[new_mdl.key] = new_mdl
    elif res == 'old':
        return mdls
    elif res == 'old_got_ward':
        old_mdl = mdls[old_key]
        if new_mdl.office:
            office = new_mdl.office[0]
            if office in old_mdl.office:
                pass
            else:
                old_mdl.office.append(office)
        if new_mdl.party:
            party = new_mdl.party[0]
            if party in old_mdl.party:
                pass
            else:
                old_mdl.party.append(party)
        if new_mdl.parl_pres:
            parl_pres = new_mdl.parl_pres[0]
            if parl_pres in old_mdl.parl_pres:
                pass
            else:
                old_mdl.parl_pres.append(parl_pres)
    elif res == 'new_got_sth':
        mdls = _update_entry(mdls, old_key, new_mdl)
    else:
        print(res)
        raise Exception('wf02, dont know how program got here.')

    return mdls


def _check_new_mdl(mdls, new_mdl):
    old_keys = list(mdls.keys())
    if new_mdl.key not in old_keys:
        new_key = new_mdl.key.split('_')[:2]
        for old_key in old_keys:
            old_key_part = old_key.split('_')[:2]
            if old_key_part == new_key:
                if new_mdl.key.split('_')[2] == 'ew':
                    if old_key.split('_')[2] != 'ew':
                        return 'old_got_ward', old_key
                elif new_mdl.parl_pres:
                    return 'new_got_sth', old_key
                else:
                    if old_key.split('_')[2] == 'ew':
                        return 'new_got_sth', old_key
        return 'new', None
    else:
        if new_mdl.party:
            return 'new_got_sth', new_mdl.key
        elif new_mdl.parl_pres:
            return 'new_got_sth', new_mdl.key
        else:
            return 'old', None


def _update_entry(mdls, old_key, new_mdl):
    old_mdl = mdls[old_key]
    if old_mdl.office:
        if new_mdl.office:
            for office in old_mdl.office:
                if office in new_mdl.office:
                    pass
                else:
                    new_mdl.office.append(office)
        else:
            new_mdl.office = old_mdl.office
    if old_mdl.party:
        if new_mdl.party:
            for party in old_mdl.party:
                if party in new_mdl.party:
                    pass
                else:
                    new_mdl.party.append(party)
        else:
            new_mdl.party = old_mdl.party
    if old_mdl.parl_pres:
        if new_mdl.parl_pres:
            for parl_pres in old_mdl.parl_pres:
                if parl_pres in new_mdl.parl_pres:
                    pass
                else:
                    new_mdl.parl_pres.append(parl_pres)
        else:
            new_mdl.parl_pres = old_mdl.parl_pres
    del mdls[old_key]
    mdls[new_mdl.key] = new_mdl

    return mdls


def _get_last_name(fields, wp):
    len_comma = len(fields.split(","))
    if len_comma > 1:
        nachName = _extract_nachName_comma(fields)
    else:
        nachName = _extract_nachName_space(fields, wp)

    if nachName:
        return nachName


def _extract_nachName_comma(fields):
    """
    Subfunctions _extract_nachName_comma and _extract_nachName_space take a
    string (fields) from bsObj as argument and extract the MdL's last name.

    There are two formats to consider:
        Old format (Wahlperiode 10 - 13):
            last_name (electoral ward) party
        New format (Wahlperiode 14 - 17):
            last_name, first_name party

        However, there are some fields that have to be checked first, i.e.
        sometimes there is an office ("Präs", "FM", ...) that needs to be
        ignored.

    This function makes use of the fact that from legislature 14 on there is
    a comma behind the last_name of the parlamentarian's name.

    Returns last_name or None
    """
    last_name = fields.split(",")[0]

    return last_name


def _extract_nachName_space(fields, wp):
    """
    The second subfunction to extract the last name from the bsObj's line.
    When this function is called, it is clear that there is no comma but
    only spaces seperating the fields.
    First find out the number of fields seperated by ' '. It's not possible
    to simply seperate at the first space and take the item at index 0
    because some names are composed like VAN UNGER etc. Finding the
    last_name is a bit tedious because of that.
    Second check until a field is either a "Wahlkreis" (city), a "Partei"
    or any other field that is not a last_name (like a title, office, ...).
    These fields are being removed.
    The remaining fields compose nachName.
    Things to consider:
        Sometimes a first name can be used as a last name:!

    Returns nachName
    """

    list_of_fields = _make_list_of_fields(fields)
    list_of_fields_to_iterate = list_of_fields

    index = 1
    while len(list_of_fields) > 1:
        len_before = len(list_of_fields)
        for field in list_of_fields_to_iterate:
            if field.startswith('AAA'):         # only cities were marked like this
                list_of_fields.remove(field)
            elif _is_it_a_party(field):
                list_of_fields.remove(field)
            elif _is_it_an_office(field, wp):
                list_of_fields.remove(field)
            elif _is_it_an_academical_title(field):
                list_of_fields.remove(field)
            elif _is_it_an_adelstitel(field):
                index = list_of_fields.index(field)
            elif _is_it_in_list_to_ignore(field):
                list_of_fields.remove(field)
        if len(list_of_fields) == len_before:
            break
    nachName = ''
    length_of_list_of_fields = len(list_of_fields) - 1
    for item in list_of_fields:
        # if we have van Helsing, we skip the "van"
        if index == 0:
            index = 1
        # if we have meyer zur heide, we want the whole name
        else:
            nachName = nachName + item
            if list_of_fields.index(item) < length_of_list_of_fields:
                nachName = nachName + " "
    if not nachName:
        print("*" * 70)
        nachName = field_list.split(" ")[0]

    if _is_it_an_office(nachName, wp):
        nachName = None

    return nachName


def _make_list_of_fields(field_list):
    field = ''
    list_of_fields = list()
    list_of_fields_to_iterate = list()
    if not '(' in field_list:
        list_of_fields = field_list.split(' ')
    else:
        fields = field_list.split('(')[0]
        list_of_fields = fields.split(' ')
        maybe_a_city = field_list.split('(')[-1]
        maybe_a_city = maybe_a_city.split(')')[0]
        if _is_it_a_city(maybe_a_city):
            maybe_a_city = 'AAA' + maybe_a_city     # mark as city with AAA
            list_of_fields.append(maybe_a_city)
        else:
            list_of_fields.append(maybe_a_city)
        fields = field_list.split(')')[-1]
        for field in fields.split(' '):
            list_of_fields.append(field)

    for field in list_of_fields:
        if field.endswith(','):
            list_of_fields_to_iterate.append(field[:-1])
        else:
            list_of_fields_to_iterate.append(field)

    list_of_fields = list_of_fields_to_iterate
    list_of_fields_to_iterate = list()
    for field in list_of_fields:
        if field and field not in list_of_fields_to_iterate:
            list_of_fields_to_iterate.append(field)

    return list_of_fields_to_iterate


def _get_wahlkreis(field_list):
    for field in field_list:
        if field.startswith('AAA'):
            wahlkreis = field[3:]
            return wahlkreis
    return 'ew'


def _is_it_a_city(field):
    """
    Find out if the field contains the name of a city in NRW. Since this
    field is usually given when two or more MdLs share the same family name,
    this is actually the city where they got elected (Wahlkreis) and is used
    to distinguish between MdLs. From Wahlperiode 14 this will be accomplished
    by their first names.
    Returns True or False
    """

    cities = _make_list_of_cities()
    is_it_a_city = _low_cap_all(field)

    if is_it_a_city in cities:
        return True
    return False


def _get_amt(field_list, wp):
    fields = list()
    for field in field_list:
        field = field.strip('(')
        field = field.strip(')')
        if _is_it_an_office(field, wp):
            fields.append(field)
    if fields:
        if len(fields) == 1:
            return fields[0]
        else:
            return fields
    else:
        return None


def _is_it_an_office(field, wp):
    """
    Find out if the field contains the name of an office.
    Returns True or False
    """

    if len(field.split(' ')) == 2 and 'GESCHÄFTSFÜHREND' in field:
        for item in field.split(' '):
            if 'GESCHÄFTSFÜHREND' not in item:
                field = item.strip()
                if field in wp.offices:
                    return True
    elif len(field.split(' ')) >= 2:
        return False

    if field in wp.offices:
        return True

    return False


def _get_adelstitel(field_list_academic, last_name):
    field_list = _make_list_of_fields(field_list_academic)
    for field in last_name.split(' '):
        if field in field_list:
            field_list.remove(field)

    peer_titles = list()
    for field in field_list:
        if _is_it_an_adelstitel(field):
            peer_titles.append(field)
    if peer_titles:
        peer_title = ''
        for title in peer_titles:
            if peer_title:
                peer_title = peer_title + ' ' + title
            else:
                peer_title = title
        return peer_title
    else:
        return None


def _is_it_an_adelstitel(field):
    """
    Find out if the field contains a title of nobility.
    Returns True or False
    """

    if field in list_of_adelstitel:
        return True
    else:
        return False


def _get_akad_titel(field_list_academic, nachName):
    field_list_to_iterate = field_list_academic.split(",")
    field_list_academic = list()
    for element in field_list_to_iterate:
        for field in element.split(" "):
            if "," in field:
                field = field[:-1]
            field_list_academic.append(field)
    field_list_to_iterate = field_list_academic

    field_list_academic = list()
    for field in field_list_to_iterate:
        if _is_it_an_academical_title(field):
            field_list_academic.append(field)

    if len(field_list_academic) == 1:
        akad_titel = field_list_academic[0]
        if _is_it_an_academical_title(akad_titel):
            return akad_titel
        else:
            return None
    elif len(field_list_academic) > 1:
        akad_titel = ""
        for field in field_list_academic:
            akad_titel = akad_titel + field
            length_of_list = len(field_list_academic)
            index_of_field = field_list_academic.index(field)
            if int(length_of_list - 1) > index_of_field:
                akad_titel = akad_titel + " "
        return akad_titel
    else:
        return None


def _is_it_an_academical_title(field):
    """
    Find out if the field contains the name of an academical title.
    Returns True or False
    """

    for titel in list_of_akad_titel:
        if titel == field:
            return True
    return False


def _get_parl_pres(field_list):
    parl_pres = None
    for field in field_list:
        if "PRÄS" in field or 'Präs' in field:
            if "(" in field and ")" in field:
                parl_pres = field[1:-1]
            elif "(" in field:
                parl_pres = field[1:]
            elif ")" in field:
                parl_pres = field[:-1]
            else:
                parl_pres = field
            return parl_pres

    return parl_pres


def _is_it_in_list_to_ignore(field):
    """
    Find out if the field contains an expression that can be ignored.
    Returns True or False
    """

    list_to_ignore = ['PRÄS)', '(MBEM)', '(GESCHÄFTSFÜHRENDER PRÄS)', 'VIZEPRÄS',\
            '(GESCHÄFTSFÜHRENDER MBEM)', 'PRÄS', '(GESCHÄFTSFÜHREND)', 'LOS',\
            'AMTPRÄS', 'VORMALS', '(VORMALS', 'GESCHÄFTSFÜHRENDER PRÄS', 'MBEM',\
            'AMTSPRÄS', 'GESCHÄFTSFÜHREND', 'GESCHÄFTSFÜHRENDE',\
            'GESCHÄFTSFÜHRENDER']

    if field in list_to_ignore:
        return True
    else:
        return False


def _get_first_name(field_list, last_name, wp):
    list_of_names = list()
    list_of_fields = field_list
    if len(last_name.split(" ")) > 1:
        for name in last_name.split(" "):
            if name in field_list:
                field_list.remove(name)
    else:
        for field in field_list:
            if field == last_name:
                field_list.remove(last_name)
                break
    for field in field_list:
        if _is_it_a_first_name(field, wp) and not _is_it_an_adelstitel(field):
            list_of_names.append(field)
        elif '-' in field:
            field1 = field.split('-')[0]
            field2 = field.split('-')[-1]
            if _is_it_a_first_name(field1, wp) or _is_it_a_first_name(field2, wp):
                vorname = field1 + '-' + field2
                list_of_names.append(vorname)

    if int(wp.wahlperiode) > 13 and len(list_of_names) == 0:
        token = False
        for field in field_list:
            if _is_it_a_party(field):
                party = field
                token = True
        if token:
            index = int(field_list.index(party))
            for field in field_list:
                if int(field_list.index(field)) < index:
                    fns = " ".join(field)
            list_of_names.append(fns)
            raise NameNotFoundError

    first_name = ''
    length_of_list_of_names = len(list_of_names) - 1
    for item in list_of_names:
        first_name = first_name + item
        if list_of_names.index(item) < length_of_list_of_names:
            first_name = first_name + ' '
    if len(list_of_names) > 0:
        return first_name
    else:
        return 'fn'


def _is_it_a_first_name(field, wp):
    """
    Find out if the field contains the name of a first name.
    Returns True or False
    """

    list_of_vornamen = _get_vornamenListe()
    field = _low_cap_all(field)

    for name in list_of_vornamen:
        if field == name:
            if field.upper() not in wp.offices:
                return True

    return False


def _get_partei(field_list):
    for field in field_list:
        if _is_it_a_party(field):
            if field == "DIE":
                partei = "DIE GRÜNEN"
            elif field == "FR.":
                partei = "FR. LOS"
            else:
                partei = field
            return partei
    return None


def _is_it_a_party(field):
    """
    Find out if the field contains the name of a party.
    Returns True or False
    """

    if field in list_of_parteien:
        return True
    else:
        return False


def _is_it_undefined(field):
    """
    Find out if the field contains sth that is not part of the name but cannot
    be defined otherwise.
    Returns True or False
    """

    if ")" in field:
        return True
    elif "(" in field:
        return True
    else:
        return False


def _mk_new_MdL(wahlperiode, last_name, first_name, electoral_ward, party,\
        office, peer_title, academic_title, parl_pres, line):
    mdl = MdL()
    mdl.legislature = wahlperiode
    mdl.first_name = first_name
    mdl.last_name = last_name
    mdl.electoral_ward = electoral_ward
    mdl.line = line
    #mdl.uid = _id()
    if office:
        mdl.office.append(office)
    if party:
        if party not in mdl.party:
            mdl.party.append(party)
    if peer_title:
        mdl.peer_title = peer_title
    if academic_title:
        mdl.academic_title = academic_title
    if parl_pres:
        if parl_pres not in mdl.parl_pres:
            mdl.parl_pres.append(parl_pres)
    key = '{}_{}_{}_{}'.format(last_name, first_name, electoral_ward, wahlperiode)
    mdl.key = key

    return mdl


def _find_missing_party(party, wahlperiode, last_name):
    """
    Add missing party to some of the cabinet's members. Those missing parties
    are found in _wer_regiert and if not already contained in MdL_dict, they
    are appended. Since some of the names are double but the party membership
    is different, containment will lead to double party memberships. Instead,
    I check if there is a party membership at all.
    Returns MdL_dict
    """

    #wahlperiode = mdl.legislature
    regPartei, regKabinett = _wer_regiert(wahlperiode)
    if last_name in regKabinett:
        if party:
            pass
        else:
            party = regKabinett[last_name]

    return party


def printout(mdl):
        print()
        print(mdl.line)
        print("Wahlperiode:", mdl.legislature)
        print("Nachname:", mdl.last_name)
        print("Vorname:", mdl.first_name)
        print("Wahlkreis:", mdl.electoral_ward)
        print("Partei:", mdl.party)
        print("Amt:", mdl.office)
        print("Adelstitel:", mdl.peer_title)
        print("Akad. Titel:", mdl.academic_title)
        print("Landtagspräsident:", mdl.parl_pres)


def _get_bsObj(wahlperiode):
    base = './parli_data/wf01_soup_objects/namenListe_WP{}.soup'
    file_loc = base.format(wahlperiode)

    with open(file_loc, "r", encoding="utf-8") as fin:
        bsObj = fin.read()

    return bsObj


def _count_total_number_of_lines(wahlperiode):
    bsObj = _get_bsObj(wahlperiode)
    IGNORE = ['BEHINDERTENBEAUFTRAGTE/R', 'DATENSCHUTZBEAUFTRAGTE/R',
               'LANDESRECHNUNGSHOF', 'LANDTAGSVERWALTUNG']

    tot = 0
    for line in bsObj.split("\n"):
        if line.startswith("<option ") and line.endswith("</option>"):
            tot += 1
        for office in IGNORE:
            if office in line:
                tot -= 1

    return tot


def _align_with_wiki(legislature, last_name, first_name, party, electoral_ward,\
        mdls_wiki, line):

    exceptions = {'10': {'MÜLLER':      {'DÜREN': 'HELMUT',
                                         'MÜLHEIM': 'GERD',
                                         'MENDEN': 'HAGEN'},
                         'HEINEMANN':   {'DORTMUND': 'HERMANN',
                                         'ENGER': 'MANFRED',
                                         'ESSEN': 'PETER'},
                         'SCHUMACHER':  {'KALL': 'WERNER',
                                         'REMSCHEID': 'ROBERT'},
                         'ALT-KÜPPERS': {'ew': 'HANS'}},
                  '11': {'SCHUMACHER':  {'KALL': 'WERNER'},
                         'PAUS':        {'BIELEFELD': 'MARIANNE',
                                         'DETMOLD': 'HEINZ'},
                         'BOULBOULLE':  {'ew': 'CARLA'},
                         'MEYER-SCHIFFER': {'ew': 'GISELA'},
                         'ALT-KÜPPERS': {'ew': 'HANS'}},
                  '12': {'KRUSE':       {'BOCHOLT': 'HEINRICH',
                                         'OLPE': 'THEODOR'},
                         'SCHULTE':     {'MENDEN': 'HUBERT',
                                         'LÜDENSCHEID': 'BERND'},
                         'LEY':         {'KÖLN': 'MARIE-THERES',
                                         'LEICHLINGEN': 'GISELA'},
                         'WALSKEN VORMALS MEYER-SCHIFFER': {'ew': 'GISELA'}},
                  '13': {'SCHULTE':     {'MENDEN': 'HUBERT',
                                         'LÜDENSCHEID': 'BERND',
                                         'GELSENKIRCHEN': 'GERD'},
                         'KRUSE':       {'BOCHOLT': 'HEINRICH',
                                         'OLPE': 'THEODOR'},
                         'WIRTZ':       {'BOCHUM': 'HEINZ',
                                         'STOLBERG': 'AXEL'},
                         'BISCHOFF':    {'MONHEIM': 'WERNER',
                                         'DUISBURG': 'RAINER'},
                         'LEY':         {'KÖLN': 'MARIE-THERES',
                                         'LEICHLINGEN': 'GISELA'},
                         'KRAFT':       {'MÜLHEIM': 'HANNELORE',
                                         'RATINGEN': 'HANS'},
                         'SCHMIDT':     {'ew': 'ULRICH'}}}

    try:
        first_name = exceptions[legislature][last_name][electoral_ward]
        return first_name
    except KeyError:
        pass

    last_name = last_name.replace('Ä', 'A')
    last_name = last_name.replace('Ö', 'O')
    last_name = last_name.replace('Ü', 'U')
    last_name = last_name.replace('ß', 'SS')

    if last_name == 'ALT-KÜPPERS':
        last_name = 'ALT-KÜPERS'
    elif last_name == 'ROBELS':
        last_name = 'ROBELS-FRÖHLICH'
    elif last_name == 'SAURE':
        last_name = 'KNOTT'

    if party == 'F.D.P.':
        party = 'FDP'
    elif party == 'DIE GRÜNEN':
        party = 'GRÜNE'

    for mdl_wiki in mdls_wiki:
        if _low_cap_all(last_name) == mdl_wiki[0].split(',')[0]:
            if electoral_ward != 'ew' and len(mdl_wiki) == 3:
                if electoral_ward == mdl_wiki[1].upper():
                    first_name = mdl_wiki[0].split(',')[-1].upper().strip()
                    return first_name
            else:
                try:
                    if party.upper() == mdl_wiki[-1].upper():
                        first_name = mdl_wiki[0].split(',')[-1]
                        first_name = first_name.upper().strip()
                        return first_name
                except TypeError:
                    print('party', party)
                    print('mdl_wiki', mdl_wiki)
                    raise Exception
                except AttributeError:
                    print('last_name, first_name', last_name, first_name)
                    print(line)
                    print('party', party)
                    print('mdl_wiki', mdl_wiki)
                    raise Exception

    return first_name


if __name__ == "__main__":
    wahlperiode = ask_for_wahlperiode()
    verbose = False
    mdls = wf02_extract_all_infos_about_MdLs(wahlperiode, verbose)
    for key, mdl in mdls.items():
        #if mdl.parl_pres:
        #    print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}, {mdl.parl_pres}')
        #print(f'{mdl.first_name} {mdl.last_name}, {mdl.party}')
        printout(mdl)

