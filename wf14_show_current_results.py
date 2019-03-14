import copy
import dill
import os
import sys

from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode


class Menu:
    '''Display options to display the contents of a specific legislature
    and its MdLs'''
    def __init__(self):
        self.legislature = _open_dilled_wp()
        self.choices = {
                "1": self.show_session_participation_of_MdLs,
                "2": self.show_all_contris,
                "3": self.show_MdLs,
                "4": self.show_key_inf_about_session,
                "5": self.show_sessions,
                "6": self.show_single_session,
                "7": self.show_session_lineup,
                "8": self.show_single_MdL,
                "9": self.quit
                }

    def display_menu(self):
        print("""
    Menu to display contents of a specific legislature and its MdLs

    1. Show participation at sessions of MdLs
    2. Show all contributions
    3. Show MdL information
    4. Show key informations about session
    5. Show sessions
    6. Show single session
    7. Show session lineup
    8. Show single MdL
    9. Quit
    """)

    def run(self):
        '''Display menu and respond to choices'''
        while True:
            self.display_menu()
            choice = input('Enter an option: ')
            action = self.choices.get(choice)
            if action:
                action()
            else:
                print('{} is not a valid choice'.format(choice))

    def show_session_participation_of_MdLs(self):
        wp = self.legislature
        for key, mdl in wp.MdLs.items():
            print(key)
            print(mdl.sessions)
            print()

    def show_all_sessions(self):
        wp = self.legislature
        for _, session in wp.sessions.items():
            _printout_session_basics(session)
            _print_speakers(session)

    def show_MdLs(self):
        wp = self.legislature
        for key, mdl in wp.MdLs.items():
            print(key)
            print(mdl)
            print()

    def show_all_contris(self):
        wp = self.legislature
        pick = input('Pick an MdL: ')
        for key, mdl in wp.MdLs.items():
            last_name = key.split('_')[0]
            if pick.upper() == last_name:
                print(key)
                for protocol_nr, contribution in mdl.contributions.items():
                    print(protocol_nr)
                    for start_end, contri in contribution.items():
                        print(start_end)
                        print(contri)
                print()

    def show_key_inf_about_session(self):
        wp = self.legislature
        sessions = dict()
        for key_tuple, session in wp.sessions.items():
            session_nr = key_tuple.protocol_nr.split('/')[-1]
            start = key_tuple.start
            end = key_tuple.end
            sessions[(start, end)] = session_nr

        for i, k in enumerate(sorted(wp.sessions, key=wp.sessions.get)):
            print(i+1, k)

    def show_sessions(self):
        wp = self.legislature
        for key_tuple, session in wp.sessions.items():
            print()
            print(key_tuple.protocol_nr, end=' ')
            print('start:', key_tuple.start, end=' ')
            print('end:', key_tuple.end)
            print(session)

    def show_single_session(self):
        wp = self.legislature
        page = input('Which pagenr should be contained in the session?\n')
        for key_tuple, session in wp.sessions.items():
            print(key_tuple)
            if int(key_tuple.start) <= int(page) <= int(key_tuple.end):
                print(key_tuple.protocol_nr, end=' ')
                print('start:', key_tuple.start, end=' ')
                print('end:', key_tuple.end)
                print(session)
                break

    def show_session_lineup(self):
        wp = self.legislature
        for key_tuple, session in wp.sessions.items():
            print()
            print(key_tuple.protocol_nr, end=' ')
            print('start:', key_tuple.start, end=' ')
            print('end:', key_tuple.end)
            _print_speakers(session)

    def show_single_MdL(self):
        wp = self.legislature
        pick = input('Pick an MdL: ')
        for key, mdl in wp.MdLs.items():
            if pick.upper() == key.split('_')[0]:
                print(mdl)
                print()

    def quit(self):
        sys.exit(0)


def _open_dilled_wp():
    '''
    '''
    wahlperiode = ask_for_wahlperiode()
    dir_loc = './parli_data/wf15_dilled_wps/'

    file_loc = dir_loc + 'WP_{}.dill'.format(wahlperiode)

    with open(file_loc, 'rb') as fin:
        wp = dill.load(fin)

    return wp


def _printout_session_basics(session):
    print(session.protocol_nr)
    print(session.date)
    print(session.url)
    print('start: {}'.format(session.start), end=' ')
    print('end: {}'.format(session.end))


def _print_speakers(session):
    print('Speakers:')
    for _, speaker in session.speakers.items():
        if isinstance(speaker.name, tuple):
            print(speaker.name[0], end=' ')
        else:
            print(speaker.name, end=' ')
        print(speaker.ward if speaker.ward else '', end=' ')
        print(speaker.party if speaker.party else '', end=' ')
        print(speaker.office if speaker.office else '', end=' ')
        print(speaker.contribution if speaker.contribution else '', end=' ')
        print(speaker.page)
    print()


if __name__ == '__main__':
    Menu().run()
