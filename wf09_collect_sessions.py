import copy
import dill
import json
import os
import reprlib
import sys

from bs4 import BeautifulSoup
from collections import namedtuple

from scraper_lib._list_of_parteien import list_of_parteien
from scraper_lib.standardize_name import _low_cap_all
from wf00_base_classes import _offices
#from wf03_mk_top_container_wahlperiode import wf03_mk_top_container_wahlperiode
#from wf04_add_search_urls_to_wp import wf04_add_search_urls_to_wp
from wf08_get_rid_of_double_speeches import wf08_get_rid_of_double_speeches



def wf09_collect_sessions(wahlperiode=False):
    '''
    Collects all data about the sessions of one legislature.
    Session = namedtuple('Session', 'url tags protocol_nr date start end speakers')
    url points to the session, it doesn't matter which parlamentarian was
    providing the link.
    tags are the key words of that session.
    protocol_nr is a unique identifier provided by the archive of the NRW parliament.
    date: the date of the session
    start: the beginning of the PDF document containing all speeches
    end: the end of the PDF document
    speakers: all the speakers who contributed to a particular session and their
    party affiliation

    Saves the newly extended wp of the chosen legislature using dill.
    '''

    try:
        if sys.argv[1] == 's':
            save = True
        else:
            save = False
    except IndexError:
        save = False

    wp = wf08_get_rid_of_double_speeches()
    legislature = wp.wahlperiode
    Session_id = namedtuple('Session_id', 'protocol_nr start end')

    dir_loc = './parli_data/wf08_speeches_bsObj/'
    file_loc = dir_loc + 'WP_{}_speeches_bsObj.dict'.format(legislature)

    with open(file_loc, 'r', encoding='utf-8') as fin:
        speeches_bsObj = json.load(fin)

    for key, mdl in wp.MdLs.items():
        mdl.speeches.collection = speeches_bsObj[key]
        for url, v in mdl.speeches.collection.items():
            nr_of_speeches = v['nr_of_speeches']
            if int(nr_of_speeches) > 0 and v['bsObj'][:5] != 'like ':
                bsObj = v['bsObj']
                for session in _extract_infos_from_bsObj(key, bsObj, wp):
                    protocol_nr = session.protocol_nr.split(' ')[-1].strip()
                    mdl.sessions.append(protocol_nr)
                    start = session.start
                    if not _is_number(start, key):
                        continue
                    start = start.strip()
                    end = session.end
                    if not _is_number(end, key):
                        continue
                    end = end.strip()
                    session_id = Session_id(protocol_nr, start, end)
                    wp.sessions[session_id] = session
                    #print(session)

    if save:
        dir_loc = './parli_data/wf09_dilled_wps/'
        if os.path.isdir(dir_loc):
            pass
        else:
            os.mkdir(dir_loc)

        file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        print('This concludes wf09 with adding the sessions particulars like date, protocol-number, start and end in the PDF document, tags, and the speakers who contributed to this session to wp.sessions and saving (dilling) wp again.')

    else:
        print('Concludes wf09: adding the session particulars to wp.sessions WITHOUT saving.')


def _is_number(n, key):
    try:
        n = n.strip()
        test = int(n)
    except ValueError:
        print('wf09, no starting page for pdf found', key)
        return False
    except AttributeError:
        print('wf09, no starting page for pdf found', key)
        return False

    return True


def _extract_infos_from_bsObj(key, bsObj, wp):

    Session = namedtuple('Session', 'url tags protocol_nr date start end speakers')
    last_name, first_name, electoral_ward, legislature = _initialize(key)

    soup = BeautifulSoup(bsObj, 'lxml')
    for table in soup.find_all('table'):
        for rows in table.find_all('tr'):
            for cells in rows.find_all('td'):
                cell = cells.find('nobr')
                try:
                    #print('cell.contents:', cell.contents)
                    box_nr = int(cell.text.strip())
                    Id = cell.find('input', attrs={'type':'checkbox'})
                    Id = str(Id).split('Id=')[-1].split('"/>')[0]
                    next_cell = cell.find_next('a', \
                            attrs={'title':'Interner Link zum Dokument'})
                    url = next_cell['href']
                    protocol_nr = next_cell.text.strip()
                    date = next_cell.next_sibling.strip().split(' ')[0]
                    fields = next_cell.next_sibling.strip().split(' ')[-2:]
                    start, end = _get_borders_of_session(fields, date)
                    if not start:
                        print(last_name, fields, protocol_nr, date)
                        #print(rows)
                        #print()
                        continue
                except AttributeError:
                    pass
                try:
                    cell = cells.find_all('br')
                    lines_of_speakers = list()
                    for line in cell:
                        while not line.find('br'):
                            line = line.next_sibling
                            if line.find('br'):
                                if 'Schlagworte:' in line:
                                    tags = line.split('Schlagworte:')[-1]
                                    tags = _normalize_tags(tags)
                                if 'Redner:' in line:
                                    lines_of_speakers.append(line)
                                elif lines_of_speakers != [] and line != []:
                                    line = line.strip()
                                    if line:
                                        lines_of_speakers.append(line)
                except AttributeError:
                    pass
            if lines_of_speakers != []:
                #print(lines_of_speakers)
                speakers = _extract_speakers(wp, lines_of_speakers)
                #print(speakers)
            session = Session(url, tags, protocol_nr, date, start, end, speakers)

            yield session


def _initialize(key):
    last_name = key.split('_')[0]
    first_name = key.split('_')[1]
    electoral_ward = key.split('_')[2]
    legislature = key.split('_')[-1]

    if last_name == 'ALT-KÜPPERS':
        last_name = 'ALT-KÜPERS'
    # This correction is necessary because ALT-KÜPERS is wrongly written
    # with two P's!

    last_name = _low_cap_all(last_name)
    if first_name == 'fn':
        first_name = False
    else:
        first_name = _low_cap_all(first_name)
    if electoral_ward == 'ew':
        electoral_ward = False
    else:
        electoral_ward = _low_cap_all(electoral_ward)

    return last_name, first_name, electoral_ward, legislature


def _normalize_tags(tags):
    normalized_tags = list()
    tags = tags.split('*')
    for tag in tags:
        normalized_tags.append(tag.strip())

    return normalized_tags


def _extract_speakers(wp, lines_of_speakers):
    speakers_of_one_session = dict()

    for i, line in enumerate(lines_of_speakers):
        Speaker = namedtuple('Speaker', 'name party ward contribution office parl_pres page')
        name, party, ward, contribution, office, parl_pres, page =\
                _speaker_details(wp, line)
        if name:
            current_speaker = Speaker(name, party, ward, contribution, office,\
                    parl_pres, page)
            speaker = 'speaker_{}'.format(i+1)
            speakers_of_one_session[speaker] = current_speaker

    if not isinstance(speakers_of_one_session, dict):
        pass
    else:
        return speakers_of_one_session


def _speaker_details(wp, line):
    ward = False
    contribution = False
    party = False
    office = False
    name = False
    page = False
    contributions = ['ZwFr', 'ZusFr', 'pErkl', 'zProt', 'KInt', 'OrdnR']
    contris_1 = ['(' + contri + ')' for contri in contributions]
    contris_2 = ['(' + contri + ' )' for contri in contributions]

    if wp.names == []:
        raise Exception('wf09, wp.names is empty!?')

    if wp.wahlperiode > 13:
        for name in wp.names:
            last_name = _low_cap_all(name[0])
            first_name = _low_cap_all(name[-1])
            if first_name in line and last_name in line:
                name = first_name + ' ' + last_name
                break
    else:
        for city in wp.wards:
            city = _low_cap_all(city)
            city_with_brackets = '(' + city + ')'
            if city_with_brackets in line:
                ward = city
                break

        for name_combi in wp.names:
            if not isinstance(name_combi, tuple):
                print(name_combi)
                print(type(name_combi))
                raise Exception('wf09, names in wp.names should be tuples')

            last_name = name_combi[0]
            if last_name == 'ALT-KÜPPERS':
                last_name = 'ALT-KÜPERS'

            last_name = _low_cap_all(last_name)
            electoral_ward = _low_cap_all(name_combi[-1])
            if electoral_ward == ward:
                if len(last_name.split(' ')) > 1:
                    if last_name in line:
                        name = last_name
                        break
                else:
                    for field in line.split(' '):
                        if '.' in field:
                            field = field.split('.')[-1]
                        if field == last_name:
                            if electoral_ward in line:
                                name = last_name
                                break
            else:
                if len(last_name.split(' ')) > 1:
                    if last_name in line:
                        name = last_name
                        break
                else:
                    for field in line.split(' '):
                        if '.' in field:
                            field = field.split('.')[-1]
                        if field == last_name:
                            name = last_name
                            break

    for partei in list_of_parteien:
        if partei in line:
            if partei == 'fr.':
                partei = 'fr. los'
            party = partei
            break

    for contri in contris_1:
        if contri in line:
            contribution = contri[1:-1]
            break
    if not contribution:
        for contri in contris_2:
            if contri in line:
                contribution = contri[1:-2]
                break

    for amt in _offices(wp.wahlperiode):
        if amt in line:
            office = amt
            break

    pres = ('PRÄS', 'VIZEPRÄS', 'GESCHÄFTSFÜHRENDER PRÄS', 'AMTPRÄS',\
            'VizePräs', 'Geschäftsführender Präs', 'Amtpräs', 'Präs',\
            'Vizepräsident', 'Vizepräsidentin', 'amt.Präs')
    for parli_presi in pres:
        if parli_presi in line:
            parl_pres = parli_presi
            break
        else:
            parl_pres = None

    for field in line.split(' '):
        if not field:
            continue
        field = _get_rid_of_pdf_markings(field)
        if not field:
            continue

        while True:
            res = _check_number(wp, field)
            if res == 0:
                break
            elif res == 1:
                page = field
                break
            elif res == 2:
                field = field[:-1]
                if not field:
                    print(line)
                    raise
                field = _get_rid_of_pdf_markings(field)
                continue
            else:
                print('field in line', field, line)
                raise

    if not page:
        print(line)
        print(field, type(field))
        raise Exception('wf09, line without page, _speaker_details')
    if not name:
        if 'Erledigt' in line:
            pass
        else:
            #elif 'Pieper' in last_name or 'Brömer' in last_name:
            print(line)
            print(name, party)
    if not party and not office and not parl_pres:
        if 'Erledigt' in line:
            pass
        else:
            print(line)

    return name, party, ward, contribution, office, parl_pres, page


def _get_rid_of_pdf_markings(field, start=False, end=False):
    if field.isdigit():
        return field
    if len(field) == 1 and field[0].isalpha():
        print('wf09, _get_rid_of_pdf_markings, field with one letter', field)
        return None
    try:
        if 'S.' in field[:2]:                               # S.1717 or S.3108BD
            field = field.replace('S.', '')                 # 1717 3108BD
        if 'l' in field:
            field = field.replace('l', '1')
        if field and field[0].isdigit() and _last_char_is_a_special_char(field):
            field = field[:-1]
        if field and field[0].isdigit() and field[-1].isalpha():      # 3108B
            field = field[:-1]
        if field and field[0].isdigit() and '-' in field:
            if start:
                field = field.split('-')[0]
            elif end:
                field = field.split('-')[-1]
            else:
                field = field.replace('-', '')
        if len(field) > 2:
            if field[0].isdigit() and field[-2].isalpha():
                field = field[:-2]
    except IndexError:
        print('field after exception', field)
        raise

    field = field.strip()
    return field


def _check_number(wp, field):
    ignores = ['Redner:', 'Dr.', 'Dr', 'Prof.', 'Dr. ', 'Dr.Dr.', 'von', 'van']

    if field.isdigit():
        return 1
    elif field[-1] == ')':          # (ZwFr)
        return 0
    elif field in ignores:
        return 0
    elif field.upper() in wp.names:
        return 0
    elif field in list_of_parteien:
        return 0
    elif field in _offices(wp.wahlperiode):
        return 0
    elif _last_char_is_a_special_char(field):
        return 2
    elif field[0].isdigit() and field[-1].isalpha():
        return 2
    else:
        return 0


def _last_char_is_a_special_char(field):
    sp_chars = [',', '-', '/', '*']
    for c in sp_chars:
        if field[-1] == c:
            return True
    return False


def _get_borders_of_session(fields, date):
    '''
    This means the borders of the whole session, as identified with the protocol
    number. A major caveat is that there may be several references, i.e.
        S.10607A-10678C,10695C
    for Wolfram Dorn in legislature 10. The link to this document will show a PDF
    document from page 10678 to page 10695, in other words a completely wrong part
    of the debate.
    This is why I decided to take the first and the last number as borders of the
    document.
    '''
    fields_to_begin_with = fields
    start = end = False
    if fields[0] == date:
        fields = fields[1:]
    elif fields == []:
        raise Exception('wf09, fields list is empty list.')

    try:
        if not fields[0]:                           # ['', 'S.9212B-']
            fields = fields[1:]
    except IndexError:
        #print(fields_to_begin_with)
        return False, False

    if len(fields) > 1:
        field_start = fields[0]
        if field_start:
            start = _get_rid_of_pdf_markings(field_start, start=True)
        field_end = fields[-1]
        if field_end:
            end = _get_rid_of_pdf_markings(field_end, end=True)
        start, end = _last_exit(start, end)
        if not start and not end:
            print('wf09, No page numbers found.')

    elif len(fields) == 1:
        field = fields[0]       # ['S.8307C,8315C-8356A'] --> S.8307C,8315C-8356A
        start, end = _get_start_and_end_field(field)
        start, end = _last_exit(start, end)

    if start and end:
        #print(f'a {fields_to_begin_with}')
        #print(f'b {start, end}')
        start = start.strip()
        end = end.strip()
        return start, end

    print('fields', fields)
    print('field', field)
    raise Exception('wf09, could not find borders of session.')


def _last_exit(start, end):
    if not start:
        start = end
    elif not end:
        end = start
    elif end == None:
        raise

    return start, end


def _get_start_and_end_field(field):
    '''
    This will concatenate split references of speeches appearing in various parts of
    a document to a single document with the lowest and highest page number being
    the start and end page of a PDF document, i.e. a reference like:
        S.8307,8315C-8356A
    will made to a single document reference with
        start:  8307
        end:    8356
    The alternative would be to make a new document for each reference, i.e. 8307 and
    8315-8356, but how would I know in advance who is actually speaking in 8307?

    Returns start and end page for the PDF document with the speeches of a session.
    '''
    comma = ','
    hyphen = '-'
    asterix = '*'
    dash = '/'
    spec_chars = [comma, hyphen, asterix, dash]
    chars = list()
    for char in field:
        if char in spec_chars:
            chars.append(char)

    if chars.count(comma) >= 1:
        field_start = field.split(comma)[0]
        field_end = field.split(comma)[-1]

        field_start = _split_field_with_spec_char(field_start, spec_chars, start=True)
        field_end = _split_field_with_spec_char(field_end, spec_chars, end=True)

    elif len(chars) <= 2:
        field_start = _split_field_with_spec_char(field, spec_chars, start=True)
        field_end = _split_field_with_spec_char(field, spec_chars, end=True)
    else:
        print(field)
        raise Exception('wf09, special chars exceeding expectation')

    try:
        if field_start:
            start = _get_rid_of_pdf_markings(field_start, start=True)
        if field_end:
            end = _get_rid_of_pdf_markings(field_end, end=True)
        start, end = _last_exit(start, end)
    except UnboundLocalError:
        print('found error')
        print(field)
        raise

    start = start.strip()
    end = end.strip()
    return start, end


def _split_field_with_spec_char(field, spec_chars, start=False, end=False):
    field_to_begin_with = field
    for char in field:
        if char in spec_chars:
            if start:
                field = field.split(char)[0]
            elif end:
                field = field.split(char)[-1]
                if field.isalpha():
                    field = field_to_begin_with.split(char)[0]
            return field
    return field


def _show_session_participation_of_MdLs(wp):
    for key, mdl in wp.MdLs.items():
        print(key)
        print(mdl.sessions)
        print()


def _adjust_bis(von_, bis_, von):
    '''
    This whole thing assumes that "bis" wasn't found and so it must be given
    a meaningful (that is bigger or equal than von) value.
    "von" is found in the block_fields, "von_" is found in the document's
    boundaries - von_ and bis_ are the start and end pages of the document.

    Returns bis or None
    '''

    bis = None                                      # to avoid UnboundLocalError
    bis_temps = list()
    if len(von_) > len(bis_):                       # like von_=321 and bis_=24
        len_bis_ = len(bis_)
        add_to_bis_ = von_[:-len_bis_]              # add_to_bis = 3
        bis_ = add_to_bis_ + bis_                   # new bis_=324
        bis = bis_
    elif len(von_) < len(bis_):                     # like von_=329 and bis_=3430
        length_bis_ = len(bis_)
        for i in range(length_bis_):
            bis_temps.append(bis_[:i] + bis_[i+1:]) # finds 430, 330, 340, 343
            for bis_temp in sorted(bis_temps):      # try to find the lowest bis_
                if bis_temp > von_:
                    bis = bis_temp
                    break
            for bis_temp in sorted(bis_temps, reverse=True):
                if bis_temp == von_:                # if speech ends on same page
                    bis = bis_temp
                    break
    try:
        if bis:
            if von_ <= von <= bis:
                return bis
    except NameError:
        if von_ <= von <= bis_:
            bis = bis_

    return bis


def test_adjust_bis():
    von_ = '328'
    bis_ = '3430'
    von = '329'
    bis = _adjust_bis(von_, bis_, von)
    assert bis == '330'

    von_ = '321'
    bis_ = '24'
    von = '322'
    bis = _adjust_bis(von_, bis_, von)
    assert bis == '324'

    von_ = '1111'
    bis_ = '1119'
    von = '1119'
    bis = _adjust_bis(von_, bis_, von)
    assert bis == None


if __name__ == '__main__':
    wf09_collect_sessions()
