import sys

from collections import namedtuple

from wf00_base_classes import Wahlperiode
from wf00_base_classes import MdL
from wf00_base_classes import Speeches
from wf03_mk_top_container_wahlperiode import wf03_mk_top_container_wahlperiode
from wf03_mk_top_container_wahlperiode import _id
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode


def wf04_add_search_urls_to_wp(wp, verbose=False):
    '''
    Search URLs are those urls that will find all speeches an MdL held in parliament.
    To construct these ursl search keys need to be made from the informations
    an MdL provides (party, office).
    These urls are then put into a namedtuple called "Speeches". There wil be
    speeches.url and speeches.collection.
    speeches.url is a list containing all urls that point to an MdL's speeches.
    speeches.collection is a dict using those urls as keys and the websites as values.
    speeches.collection will be filled later.
    '''

    for _, mdl in wp.MdLs.items():
        legislature = mdl.legislature
        search_keys = list()
        urls = list()

        for search_key in _create_search_key(mdl, verbose):
            if search_key not in search_keys:
                search_keys.append(search_key)
        for search_key in search_keys:
            search_url = _combine_search_url(search_key, legislature)
            if not urls:
                urls = [search_url]
            elif search_url not in urls:
                urls.append(search_url)
        mdl.speeches = Speeches()
        mdl.speeches.urls = urls
        mdl.speeches.collection = dict()    # shouldn't that be declared in wf00?

    print('Concludes wf04 and returns wp with urls (to search for speeches) added to mdl.speeches')

    return wp


def _create_search_key(mdl, verbose):
    """
    The url to search the speeches needs a search key that contains names,
    nobility titles, office or party, and offices AND party memberships.
    It is inevitable that a few search keys will lead to errors or messages
    that nothing was found.
    Search key is a string and will look like this:
        'NACHNAME+PARTEI'
        'NACHNAME+VORNAME+PARTEI'
        'VON+NACHNAME+PARTEI'                       leg 10
        'NACHNAME+VORNAME+VON+PARTEI'               leg 14
        'NACHNAME+VORNAME+AMT'
        'NACHNAME+VORNAME+AMT+PARTEI'
        ...

    Yields search_key
    """

    search_keys = list()
    legislature = mdl.legislature
    if legislature in ['10', '11']:
        if verbose:
            print(mdl.key)
        for search_key in _make_search_key_leg10_11(mdl):
            if search_key not in search_keys:
                search_keys.append(search_key)
                if verbose:
                    print(search_key)
                yield search_key
            else:
                pass
        if verbose:
            print()
    elif legislature in ['12', '13']:
        if verbose:
            print(mdl.key)
        for search_key in _make_search_key_leg12_13(mdl):
            if search_key not in search_keys:
                search_keys.append(search_key)
                if verbose:
                    print(search_key)
                yield search_key
            else:
                pass
        if verbose:
            print()
    elif legislature in ['14', '16']:
        if verbose:
            print(mdl.key)
        for search_key in _make_search_key_leg14_16(mdl):
            if search_key not in search_keys:
                search_keys.append(search_key)
                if verbose:
                    print(search_key)
                yield search_key
            else:
                pass
        if verbose:
            print()
    elif legislature == '15':
        if verbose:
            print(mdl.key)
        for search_key in _make_search_key_leg15(mdl):
            if search_key not in search_keys:
                search_keys.append(search_key)
                if verbose:
                    print(search_key)
                yield search_key
            else:
                pass
        if verbose:
            print()


def _get_name(mdl):
    legislature = mdl.legislature
    if int(legislature) > 13:
        last_name = _join_parts(mdl.last_name)
        first_name = _join_parts(mdl.first_name)
        full_name = last_name + '+' + first_name
    else:
        full_name = _join_parts(mdl.last_name)
        if 'VORMALS' in mdl.last_name:
            full_name = 'WALSKEN+VORMALS+MEYER-SCHIFFER'

    return full_name


def _join_parts(mdl_field):
    field = ''
    for part in mdl_field.split(' '):
        part = _make_utf8_literals_visible(part)
        if field:
            field = field + '+' + part
        else:
            field = part

    return field


def _make_search_key_leg10_11(mdl):
    ward = parl_pres = offices = ''
    search_key = ''
    key_so_far = ''

    if mdl.party:
        parties = _get_parties(mdl)
    if mdl.parl_pres:
        parl_pres =  _get_parli_presis(mdl)[0]
    if mdl.electoral_ward != 'ew':
        ward = _make_utf8_literals_visible(mdl.electoral_ward)
    if mdl.office:
        offices = mdl.office

    if mdl.peer_title:
        peer_title = _join_parts(mdl.peer_title)
        key_so_far = peer_title

    name = _get_name(mdl)
    if key_so_far:
        key_so_far = key_so_far + '+' + name
    else:
        key_so_far = name

    for party in parties:
        if ward and parl_pres:
            search_key = key_so_far + '+' + ward + '+' + parl_pres + '+' + party
            yield search_key
        elif ward:
            search_key = key_so_far + '+' + ward + '+' + party
            yield search_key
        elif parl_pres:
            search_key = key_so_far + '+' + parl_pres + '+' + party
            yield search_key

        if ward and offices:
            for offi in offices:
                search_key = key_so_far + '+' + ward + '+' + offi + '+' + party
                yield search_key
                search_key = key_so_far + '+' + ward + '+' + offi
                yield search_key
        elif ward:
            search_key = key_so_far + '+' + ward + '+' + party
            yield search_key
        elif offices:
            for offi in offices:
                search_key = key_so_far + '+' + offi + '+' + party
                yield search_key
                search_key = key_so_far + '+' + offi
                yield search_key

        if not ward:
            search_key = key_so_far + '+' + party
            yield search_key


def _make_search_key_leg12_13(mdl):
    ward = parl_pres = offices = ''
    parties = list()
    offices = list()
    search_key = ''

    if mdl.electoral_ward != 'ew':
        ward = _make_utf8_literals_visible(mdl.electoral_ward)
    if mdl.office:
        offices = _get_offices(mdl)

    name = _get_name(mdl)
    if mdl.party:
        parties = _get_parties(mdl)
    if mdl.parl_pres:
        parl_pres =  _get_parli_presis(mdl)

    for party in parties:
        if ward and parl_pres and party:
            for parli_presi in parl_pres:
                search_key = name + '+' + ward + '+' + parli_presi + '+' + party
                yield search_key
        elif ward:
            search_key = name + '+' + ward + '+' + party
            yield search_key
        elif parl_pres:
            for parli_presi in parl_pres:
                search_key = name + '+' + parli_presi + '+' + party
                yield search_key

        if ward and offices:
            for offi in offices:
                search_key = name + '+' + ward + '+' + offi + '+' + party
                yield search_key
        elif ward:
            search_key = name + '+' + ward + '+' + party
            yield search_key
        elif offices:
            for offi in offices:
                search_key = name + '+' + offi
                yield search_key

        if not ward:
            search_key = name + '+' + party
            yield search_key


def _make_search_key_leg14_16(mdl):
    ward = parl_pres = offices = ''
    search_key = ''
    peer_title = ''

    if mdl.party:
        parties = _get_parties(mdl)
    if mdl.parl_pres:
        parl_pres =  _get_parli_presis(mdl)[0]
    if mdl.office:
        offices = _get_offices(mdl)
    if mdl.peer_title:
        peer_title = _join_parts(mdl.peer_title)

    name = _get_name(mdl)
    if peer_title:
        name = name + '+' + peer_title

    try:
        for party in parties:
            if parl_pres:
                search_key = name + '+' + parl_pres + '+' + party
                yield search_key
                search_key = name + '+' + parl_pres
                yield search_key
                search_key = name + '+' + party
                yield search_key
            elif offices:
                for offi in offices:
                    search_key = name + '+' + offi + '+' + party
                    yield search_key
                    search_key = name + '+' + offi
                    yield search_key
                search_key = name + '+' + party
                yield search_key
            else:
                search_key = name + '+' + party
                yield search_key
    except UnboundLocalError:
        if parl_pres:
            search_key = name + '+' + parl_pres
            yield search_key
        elif offices:
            for offi in offices:
                search_key = name + '+' + offi
                yield search_key


def _make_search_key_leg15(mdl):
    ward = parl_pres = offices = ''
    search_key = ''
    peer_title = ''

    if mdl.party:
        parties = _get_parties(mdl)
    if mdl.parl_pres:
        parl_pres =  _get_parli_presis(mdl)[0]
    if mdl.office:
        offices = _get_offices(mdl)
    if mdl.peer_title:
        peer_title = _join_parts(mdl.peer_title)

    name = _get_name(mdl)
    if peer_title:
        name = name + '+' + peer_title

    try:
        for party in parties:
            if parl_pres:
                search_key = name + '+' + parl_pres + '+' + party
                yield search_key
                search_key = name + '+' + parl_pres
                if mdl.last_name == 'DINTHER':
                    executive = _make_utf8_literals_visible('GESCHÄFTSFÜHREND')
                    search_key = search_key + '+' + executive
                yield search_key
                search_key = name + '+' + party
                yield search_key
            elif offices:
                for offi in offices:
                    search_key = name + '+' + offi + '+' + party
                    yield search_key
                    search_key = name + '+' + offi
                    yield search_key
                search_key = name + '+' + party
                yield search_key
            else:
                search_key = name + '+' + party
                yield search_key
    except UnboundLocalError:
        if parl_pres:
            search_key = name + '+' + parl_pres
            yield search_key
        elif offices:
            for offi in offices:
                search_key = name + '+' + offi
                yield search_key


def _get_parli_presis(mdl):
    parli_presis = list()
    for parli_presi in mdl.parl_pres:
        if len(parli_presi.split(' ')) > 1:
            # this takes care of "geschäftsführend"
            executive = _make_utf8_literals_visible(parli_presi.split(' ')[0])
            parli_presi = _make_utf8_literals_visible(parli_presi.split(' ')[-1])
            parli_presis.append(executive + '+' + parli_presi)
        else:
            parli_presi = _make_utf8_literals_visible(parli_presi)
        parli_presis.append(parli_presi)

    return parli_presis


def _get_offices(mdl):
    offices = list()
    for office in mdl.office:
        if len(office.split(' ')) > 1:
            # this takes care of "geschäftsführend"
            if 'GESCHÄFTS' in office.split(' ')[0]:
                executive = _make_utf8_literals_visible(office.split(' ')[0])
                office = _make_utf8_literals_visible(office.split(' ')[-1])
                offices.append(executive + '+' + office)
            elif 'GESCHÄFTS' in office.split(' ')[-1]:
                executive = _make_utf8_literals_visible(office.split(' ')[-1])
                office = _make_utf8_literals_visible(office.split(' ')[0])
                offices.append(office + '+' + executive)
            else:
                offices.append(_make_utf8_literals_visible(office))
        else:
            office = _make_utf8_literals_visible(office)
            offices.append(office)

    return offices


def _get_parties(mdl):
    parties = list()

    for party in mdl.party:
        if 'F.D.P.' in party or 'F.D.P' in party:
            party = 'F+D+P'
            parties.append(party)
        elif 'DIE GRÜNEN' in party:
            party = _make_utf8_literals_visible('GRÜNEN')
            party = 'DIE+' + party
            parties.append(party)
        elif 'FR. LOS' in party:
            party = 'FR+LOS'
            parties.append(party)
        else:
            party = _make_utf8_literals_visible(party)
            parties.append(party)

    return parties


def _make_utf8_literals_visible(name):
    # https://www.utf8-chartable.de/unicode-utf8-table.pl
    if "ß" in name:
        name = name.replace("ß", "%DF")
    if "Ä" in name:
        name = name.replace("Ä", "%C4")
    if "Ö" in name:
        name = name.replace("Ö", "%D6")
    if "Ü" in name:
        name = name.replace("Ü", "%DC")
    if "É" in name:
        name = name.replace("É", "%C9")

    return name


def _combine_search_url(search_key, wahlperiode):
    """
    Search_key and wahlperiode are concatenated with two given strings to a
    search url.
    Returns search_url
    """
    base = "https://www.landtag.nrw.de/portal/WWW/Webmaster/GB_II/II.2/Suche/Landtagsdokumentation_ALWP/Suchergebnisse_Ladok.jsp?&mn=1606dfe0c2a&wp={}&w=native%28%27%28name+phrase+like+%27%27".format(
        wahlperiode
    )
    end = "%27%27%29+and+%28dokart+phrase+like+%27%27PlPr%27%27%29%27%29&order=native%28%27DOKDATUM%281%29%2FDescend+%27%29&&view=detail&maxRows=1000"
    search_url = base + search_key + end
    return search_url


if __name__ == "__main__":
    print(sys.version)
    wp = wf03_mk_top_container_wahlperiode()
    wp = wf04_add_search_urls_to_wp(wp, verbose=True)
    #if verbose:
    #    for key in wp.MdLs:
    #        mdl = wp.MdLs[key]
    #        if mdl.office:
    #            print(mdl)
    #        elif mdl.parl_pres:
    #            print(mdl)
