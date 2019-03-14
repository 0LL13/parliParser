from collections import namedtuple

import reprlib


class NameNotFoundError(BaseException):
    '''
    Raised when a name for a parlamentarian could not be retreived from
    the bsObj that contained all the names.
    '''


class Wahlperiode:
    '''
    The base class for the legislature periods.
    Collects parlamentarians, sessions, ministries, offices.
    '''
    MdLs = dict()
    sessions = dict()
    ministry = dict()
    offices = list()
    number_of_MdLs = int
    last_names = list()
    first_names = list()
    names = list()      # tuples of complete names with first and last name
    wards = list()

    def __init__(self, legislature):
        self.wahlperiode = legislature
        cls = self.__class__
        self.MdLs = cls.MdLs
        self.sessions = cls.sessions
        self.ministry = cls.ministry
        offices = _offices(legislature)
        self.offices = offices
        self.number_of_MdLs = cls.number_of_MdLs
        self.last_names = cls.last_names
        self.first_names = cls.first_names
        self.names = cls.names
        self.wards = cls.wards


def _offices(wp):
    if wp not in range(10, 18):
        raise Exception('Parameter must be int between 10 and 17.')

    offices_wp10 = ['MP', 'FM', 'IM', 'JM', 'KM', 'MAGS', 'MBA', 'MSWV', 'MURL',\
                    'MWMT', 'MWF']
    offices_wp11 = ['MP', 'FM', 'IM', 'JM', 'KM', 'MAGS', 'MBW', 'MFBA', 'MBA',\
                    'MGFM', 'MSV', 'MURL', 'MWMT', 'MWF']
    offices_wp12 = ['MP', 'FM', 'IM', 'JM', 'MIJ', 'MAGS', 'MBW', 'MBEA', 'MGFM',\
                    'MSW', 'MSWWF', 'MSKS', 'MASSKS', 'MURL', 'MFBA', 'MWMTV',\
                    'MWF', 'MFJFG', 'MSV', 'MfbA']
    offices_wp13 = ['MP', 'FM', 'IM', 'JM', 'MASQT', 'MWA', 'MBE', 'MWF',\
                    'MFJFG', 'MGSFF', 'MSWF', 'MSWKS', 'MUNLV', 'MVEL', 'MWMEV',\
                    'MSJK', 'MBEM', 'CDS', 'CdS']
    offices_wp14 = ['MP', 'MIWFT', 'FM', 'IM', 'JM', 'MAGS', 'MGFFI', 'MSW',\
                    'MBE', 'MBEM', 'MUNLV', 'MBV', 'MWME']
    offices_wp15 = ['MP', 'FM', 'MIK', 'JM', 'MWEBWV', 'MIWF', 'MAIS', 'MFKJKS',\
                    'MSW', 'MKULNV', 'MGEPA', 'MBEM']
    offices_wp16 = ['MP', 'MSW', 'FM', 'MWEIMH', 'MIK', 'MAIS', 'JM', 'MKULNV',\
                    'MBWSV', 'MIWF', 'MFKJKS', 'MGEPA', 'MBEM', 'MCDS', 'MCdS']
    offices_wp17 = ['MP', 'MKFFI', 'FM', 'IM', 'MWIDE', 'MAGS', 'MSB', 'MHKBG',\
                    'JM', 'VM', 'MULNV', 'MKW', 'MBEI', 'MBEIM']

    # CdS: Chef der Staatskanzlei

    offices = {'offices_wp10': offices_wp10,
               'offices_wp11': offices_wp11,
               'offices_wp12': offices_wp12,
               'offices_wp13': offices_wp13,
               'offices_wp14': offices_wp14,
               'offices_wp15': offices_wp15,
               'offices_wp16': offices_wp16,
               'offices_wp17': offices_wp17}
    for key, value in offices.items():
        if str(wp) in key:
            return value


class MdL:
    '''Basic informations about a parlamentarian'''

    def __init__(self):
        cls = self.__class__
        self.key = str
        self.legislature = int
        self.electoral_ward = False
        self.first_name = str
        self.last_name = str
        self.academic_title = False
        self.peer_title = False
        self.party = list()
        self.office = list()
        self.speeches = Speeches()
        self.sessions = list()
        self.contributions = dict()
        self.parl_pres = list()
        self.line = str
        self.uid = False

    def __repr__(self):
        horizontal = '{}\n'.format('-'*52)
        key = '| Key: {}\n'.format(self.key)
        legislature = '| Legislature period:\t\t\t{}\n'.format(self.legislature)
        last_name = '| Last name:\t\t\t\t{}\n'.format(self.last_name)
        if self.first_name != 'fn':
            first_name = '| First name:\t\t\t\t{}\n'.format(self.first_name)
        else:
            first_name = ''
        if self.electoral_ward != 'ew':
            electoral_ward = '| Electoral ward:\t\t\t{}\n'.format(
                    self.electoral_ward)
        else:
            electoral_ward = ''
        academic_title = f'| Academic title:\t\t\t{self.academic_title}\n'
        peer_title = f'| Peer title:\t\t\t\t{self.peer_title}\n'
        party = f'| Party:\t\t\t\t{self.party}\n'
        office = f'| Office:\t\t\t\t{self.office}\n'
        sessions = f'| Sessions:\t\t\t\t{self.sessions}\n'
        speeches = f'| Speeches:\t\t\t{self.speeches}\n'
        parl_pres = f'| Parliament president:\t\t\t{self.parl_pres}\n'
        #uid = f'| Unique ID:\t\t\t\t{self.uid}\n'
        line = f'| line:\t{self.line}\n'
        contris = f'| Contributions: {self.contributions}\n'

        mdl = '{0}{1}{2}{3}{4}{5}{6}{7}{8}{9}{10}{11}{12}{13}{14}{15}{16}'.format(
                                                        horizontal,
                                                        key,
                                                        last_name,
                                                        first_name,
                                                        electoral_ward,
                                                        horizontal,
                                                        academic_title,
                                                        peer_title,
                                                        party,
                                                        office,
                                                        sessions,
                                                        speeches,
                                                        parl_pres,
                                                        legislature,
                                                        line,
                                                        contris,
                                                        horizontal)
        return mdl


class Speeches:
    '''
    Complete collection of speeches of an MdL within a legislature period.
    url points to the NRW parliament's archive
    '''

    Speeches = namedtuple('Speeches', 'urls collection')

    def __init__(self):
        cls = self.__class__
        self.urls = self.Speeches.urls
        self.collection = self.Speeches.collection

    def __repr__(self):
        Speeches = '\n\t{}\n\t{}'.format(
                reprlib.repr(self.urls),
                reprlib.repr(self.collection))

        return Speeches


