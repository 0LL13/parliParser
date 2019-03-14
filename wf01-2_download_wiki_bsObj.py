import requests
import os.path

from bs4 import BeautifulSoup
from parli_data.sourceBox import headers
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode


def wf01_save_wiki_bsObj():
    """
    Gets source code of the site

    https://de.wikipedia.org/wiki/Liste_der_Mitglieder_des_Landtages_Nordrhein-Westfalen_(17._Wahlperiode)

    at the Wikipedia with all the parlamentarians (MdLs) of a given
    "Wahlperiode" (legislature).

    The url and the legislature will be asked for. Currently there are
    Wahlperiode 10 to 17 available.
    Returns nothing, but saves the bsObj as a file for further use.

    Saves: wikiListe_WP10.soup - wikiListe_WP17.soup
    Returns: True, if bsObj is downloaded and saved, otherwise False
    """

    url_with_all_MdLs = 'https://de.wikipedia.org/wiki/Liste_der_Mitglieder_des_Landtages_Nordrhein-Westfalen_({}._Wahlperiode)'

    wahlperiode = ask_for_wahlperiode()
    url = url_with_all_MdLs.format(wahlperiode)
    print(url)

    dir_loc = "./parli_data/wf01_soup_objects/"
    file_loc = dir_loc + "wikiListe_WP{}.soup".format(wahlperiode)
    if os.path.isdir(dir_loc):
        if os.path.exists(file_loc):
            check = input("File exists, overwrite? y/n")
            if check == "y":
                if _download_and_save_bsObj(url, file_loc, wahlperiode):
                    return True
        else:
            if _download_and_save_bsObj(url, file_loc, wahlperiode):
                return True
    else:
        os.mkdir(dir_loc)
        if _download_and_save_bsObj(url, file_loc, wahlperiode):
            return True

    return False


def _download_and_save_bsObj(url, file_loc, wahlperiode):
    session = requests.Session()
    try:
        req = requests.get(url, headers=headers[1])
    except requests.exceptions.ConnectionError:
        print('ConnectionError, no download')
        return False

    bsObj = BeautifulSoup(req.text, "lxml")

    with open(file_loc.format(wahlperiode), "w") as fout:
        fout.write(str(bsObj))

    return True


if __name__ == "__main__":
    print(wf01_save_wiki_bsObj())
