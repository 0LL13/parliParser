import copy
import dill
import os
import sys

from collections import namedtuple
from collections import defaultdict
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib.standardize_name import _low_cap_all


def wf12_find_MdLs_speeches():
    '''
    Function wf12 attributes the session particulars like protocol-number,
    start and end in the PDF document, actual party affiliation, and the kind
    of contribution to the speaker in mdl.contributions and saving (dilling)
    wp again.
    '''

    try:
        if sys.argv[1] == 's':
            save = True
        else:
            save = False
    except IndexError:
        save = False

    wp = _open_dilled_wp()
    for _, mdl in wp.MdLs.items():
        sessions = _collect_session_participation_of_MdL(mdl, wp)
        mdl.contributions = _find_MdL_in_lineup(mdl, sessions, wp)

    if save:
        dir_loc = './parli_data/wf12_contributions/'
        if os.path.isdir(dir_loc):
            pass
        else:
            os.mkdir(dir_loc)

        legislature = wp.wahlperiode
        file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        print('This concludes wf12 with attributing the session particulars')
        print('like protocol-number, start and end in the PDF document, actual')
        print('party affiliation, and the kind of contribution to the speaker')
        print('in mdl.contributions and saving (dilling) wp again.')

    else:
        print('Concludes wf12 WITHOUT saving.')

    return wp


def _collect_session_participation_of_MdL(mdl, wp):
    for key in wp.MdLs:
        if wp.MdLs[key] == mdl:
            return mdl.sessions


def _find_MdL_in_lineup(mdl, sessions, wp):
    legislature = wp.wahlperiode
    sittings = list()
    session_merger = defaultdict()
    mdl_key = mdl.key
    last_name = _low_cap_all(mdl_key.split('_')[0])
    first_name = _low_cap_all(mdl_key.split('_')[1])

    if mdl_key.split('_')[2] != 'ew':
        ward = _low_cap_all(mdl_key.split('_')[2])
    else:
        ward = 'ew'
    mdl = (last_name, first_name, ward)
    counter = 1

    for session in sessions:
        if session not in sittings:
            sittings.append(session)
    #print(f'MdL {mdl_key} attended {len(sittings)} sessions')

    for key_tuple, session in wp.sessions.items():
        #print('key_tuple', key_tuple)
        #print('session', session)
        #print()
        session_nr = session.protocol_nr.split(' ')[-1]
        mdls = wp.sessions[key_tuple].speakers
        lineup = None
        if session_nr in sittings:
            if session_nr not in session_merger:
                session_merger[session_nr] = dict()
            for _, MdL in mdls.items():
                if int(legislature) < 14:
                    if MdL.ward and MdL.ward != 'ew':
                        if MdL.name == last_name:
                            start = key_tuple.start
                            end = key_tuple.end
                            if end:
                                start_end = start + ', ' + end
                            else:
                                start_end = start
                            session_merger[session_nr][start_end] = mdls
                    elif MdL.name == last_name:
                        start = key_tuple.start
                        end = key_tuple.end
                        if end:
                            start_end = start + ', ' + end
                        else:
                            start_end = start
                        session_merger[session_nr][start_end] = mdls
                elif int(legislature) >= 14:
                    name = first_name + ' ' + last_name
                    if MdL.name == name:
                        start = key_tuple.start
                        end = key_tuple.end
                        if end:
                            start_end = start + ', ' + end
                        else:
                            start_end = start
                        session_merger[session_nr][start_end] = mdls

    contris = dict()
    for session_nr, sessions in session_merger.items():
        for start_end, speakers in sessions.items():
            #_printout_lineup(session_nr, start_end, speakers)
            contri = _collect_mdl_contributions(contris, session_nr, mdl,\
                    start_end, speakers, legislature)


    return contris


def _printout_lineup(session_nr, start_end, speakers):
    print(session_nr, start_end)
    for _, speaker in speakers.items():
        print(speaker.name, end=' ')
        if speaker.party:
            print(speaker.party, end=' ')
        if speaker.ward:
            print(speaker.ward, end=' ')
        if speaker.office:
            print(speaker.office, end=' ')
        if speaker.contribution:
            print(speaker.contribution, end=' ')
        print(speaker.page)
    print()


def _collect_mdl_contributions(contris, session_nr, mdl, start_end, speakers,\
        legislature):
    end = start_end.split(',')[-1]
    #print(start_end, end)
    last_name = mdl[0]
    first_name = mdl[1]
    name = first_name + ' ' + last_name
    ward = mdl[-1]

    try:
        if contris[session_nr]:
            pass
    except KeyError:
        contris[session_nr] = dict()
    c = contris[session_nr]

    lineup = list()
    for _, speaker in speakers.items():
            contri_end = False
            if int(legislature) < 14:
                if ward != 'ew':
                    if speaker.ward == ward:
                        c = _mk_contri_entry(speaker, last_name, speakers,\
                                contri_end, end, c)
                elif speaker.name == last_name:
                    c = _mk_contri_entry(speaker, last_name, speakers,\
                            contri_end, end, c)
            else:
                if speaker.name == name:
                    c = _mk_contri_entry(speaker, name, speakers, contri_end, end, c)

    return c


def _mk_contri_entry(speaker, name, speakers, contri_end, end, c):
    '''
    This will decide which pages to look at in a PDF document.
    Tricky: at 14/114 there will be MdL Wolf speaking before MdL Altenkamp at
    page 13293. Altenkamp will also speak at 13293 until page 13294, when MdL
    Wolf will speak one more time. How can I prevent
    '''
    if speaker.name == name:
        start  = speaker.page
        start = start.strip()
        contri = speaker.contribution
        found_speaker = False
        if not contri:
            for _, s in speakers.items():
                if s.name == name and s.page == start:
                    found_speaker = True
                if found_speaker:
                    if int(s.page) >= int(start) and s.name != name:
                        if not s.contribution:
                            contri_end = s.page
                            contri_end = contri_end.strip()
                            break
        else:
            for _, s in speakers.items():
                if s.name == name and s.page == start:
                    found_speaker = True
                if found_speaker:
                    if int(s.page) >= int(start) and s.name != name:
                        contri_end = s.page
                        contri_end = contri_end.strip()
                        break

        if not contri_end:
            contri_end = end
            contri_end = contri_end.strip()
        c[(start, contri_end)] = dict()
        if contri:
            kee = f'{contri}_{speaker.party}'
            c[(start, contri_end)][kee] = 'actual contribution'
        elif speaker.party:
            kee = speaker.party
            c[(start, contri_end)][kee] = 'actual contribution'
        elif speaker.office:
            kee = speaker.office
            c[(start, contri_end)][kee] = 'actual contribution'
        elif speaker.parl_pres:
            kee = speaker.parl_pres
            c[(start, contri_end)][kee] = 'actual contribution'
        elif not speaker.party and not speaker.office and not speaker.parl_pres:
            print(speaker)
            raise

    return c


def show_sessions(self):
    wp = self.legislature
    for key_tuple, session in wp.sessions.items():
        print()
        print(key_tuple.protocol_nr, end=' ')
        print('start:', key_tuple.start, end=' ')
        print('end:', key_tuple.end)
        print(session)


def show_session_lineup(self):
    wp = self.legislature
    for key_tuple, session in wp.sessions.items():
        print()
        print(key_tuple.protocol_nr, end=' ')
        print('start:', key_tuple.start, end=' ')
        print('end:', key_tuple.end)
        _print_speakers(session)


def _single_MdL(wp):
    '''
    Caveat: some MdLs have the same family name. Until legislature 13 they are
    identified by their electoral ward, from leg 14 on they come with their
    first names.
    So this means I will have one method for leg < 14 and one for leg >= 14.
    '''

    pick = input('Pick an MdL (last name only): ')
    name = pick
    if 'ß' in pick:
        pick = pick.split('ß')[0].upper() + 'ß' + pick.split('ß')[-1].upper()
    else:
        pick = pick.upper()
    print(pick)
    mdls = list()
    for key, mdl in wp.MdLs.items():
        if pick == key.split('_')[0]:
            print('Picking: ', key)
            mdls.append((mdl, key))

    if len(mdls) == 1:
        mdl = mdls[0][0]
        key = mdls[0][-1]
        return mdl
    elif len(mdls) > 1:
        print('There are two or more MdLs with that name.')
        for key, mdl in wp.MdLs.items():
            if int(wp.wahlperiode) < 14:
                if mdl.electoral_ward != 'ew':
                    for mdl in mdls:
                        mdl = mdl[0]
                        print('Do you mean {}, {}?'.format(mdl.last_name,\
                                mdl.electoral_ward))
                    ward = input('Please enter electoral ward: ')
                    for key, mdl in wp.MdLs.items():
                        if mdl.electoral_ward == ward.upper():
                            mdl.key = key
                            print(key)
                            return mdl
                    print('Enter ward as shown.')
                    sys.exit()
            else:
                for mdl in mdls:
                    mdl = mdl[0]
                    print('Do you mean {}, {}?'.format(mdl.last_name, mdl.first_name))
                first_name = input('Enter first name: ')
                for key, mdl in wp.MdLs.items():
                    if mdl.last_name == pick.upper():
                        if mdl.first_name == first_name.upper():
                            mdl.key = key
                            print(key)
                            return mdl
                    print('Enter first names as shown.')
                    sys.exit()


    print('{} not an MdL of legislature {}'.format(pick, wp.wahlperiode))
    return None


def _open_dilled_wp():
    '''
    '''
    wahlperiode = ask_for_wahlperiode()
    dir_loc = './parli_data/wf09_dilled_wps/'
    file_loc = dir_loc + 'WP_{}.dill'.format(wahlperiode)

    with open(file_loc, 'rb') as fin:
        wp = dill.load(fin)

    return wp


def _check_if_all_contris(wp):
    for _, mdl in wp.MdLs.items():
        print(mdl.key)
        for k, v in mdl.contributions.items():
            print(f'{k}: {v}')
        print()
        check = input('Continue? ./n')
        if check == 'n':
            sys.exit()


if __name__ == '__main__':
    wp = wf12_find_MdLs_speeches()

    check = input('Do you want to check if the contributions are in place? y/.')
    if check == 'y':
        check = input('Single MdLs or all of them? 1=single, 2=all')
        if check == '2':
            _check_if_all_contris(wp)
        else:
            token = True
            while token:
                mdl = _single_MdL(wp)
                token = False

            if mdl:
                sessions = _collect_session_participation_of_MdL(mdl, wp)
                contris = _find_MdL_in_lineup(mdl, sessions, wp)
                for k, v in contris.items():
                    print(f'{k}: {v}')
            else:
                choice = input('See all MdLs of {}? (y/.) '.format(wp.wahlperiode))
                if choice == 'y':
                    for _, mdl in wp.MdLs.items():
                        print(mdl.last_name, end=', ')
                    print()
