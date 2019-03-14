import copy
import dill
import os
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode


def wf11_download_session_pdfs():
    '''
    '''
    wahlperiode = ask_for_wahlperiode()
    dir_loc = './parli_data/'
    dir_loc = dir_loc + 'wf11_sessions/WP{}/'.format(wahlperiode)
    if not os.path.isdir(dir_loc):
        os.makedirs(dir_loc)

    urls = _create_session_urls(wahlperiode)
    url_base = 'https://www.landtag.nrw.de/portal/WWW/dokumentenarchiv/Dokument?Id='
    for url in urls:
        url_name = url.split('?Id=')[-1] + '.pdf'
        file_loc = dir_loc + url_name
        if os.path.isfile(file_loc):
            print('.', end='')
            pass
        else:
            url = url_base + url.split('Id=')[-1]
            response = _get_response(url)
            print('*', end='')
            with open(file_loc, 'wb') as fout:
                fout.write(response.content)
    print()
    return None


def _create_session_urls(wahlperiode=False):
    '''
    '''
    dir_loc = './parli_data/wf09_dilled_wps/'
    file_loc = dir_loc + 'WP_{}.dill'.format(wahlperiode)

    with open(file_loc, 'rb') as fin:
        wp = dill.load(fin)

    urls = list()
    for nr, session in wp.sessions.items():
        if '&' in session.url:
            base = session.url.split('?Id=')[0] + '?'
            for url in session.url.split('&'):
                if 'WWW' in url:
                    if url not in urls:
                        urls.append(url)
                else:
                    url = base + url
                    if url not in urls:
                        urls.append(url)
        else:
            if session.url not in urls:
                urls.append(session.url)

    return urls


def requests_retry_session(
        retries=3,
        backoff_factor=0.8,
        status_forcelist=(500, 502, 504),
        session=None,
        headers=None,
        ):
    '''
    https://www.peterbe.com/plog/best-practice-with-retries-with-requests
    Setup to retry a url a sensible number of times and quit knowing why it
    didn't work.
    '''
    session = session or requests.Session()
    retry = Retry(
            total=retries,
            read=retries,
            connect=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def _get_response(url):
    headers = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)\
                             AppleWebKit 537.36 (KHTML, like Gecko) Chrome",
               "Accept":"html,application/xhtml+xml,application/xml;\
                         q=0.9,image/webp,*/*;q=0.8"}
    try:
        session = requests_retry_session()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as err:
        print(err)
        dir(err)
    except requests.exceptions.Timeout as err:
        print(err.arg[0])
    except requests.exceptions.RequestException as e:
        print('Catastrophic error at {}'.format(url))
        print(e)
        sys.exit(1)


if __name__ == '__main__':
    wf11_download_session_pdfs()
