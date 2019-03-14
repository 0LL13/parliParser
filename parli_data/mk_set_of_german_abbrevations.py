# Abbrevations found here:

# https://www.bundesanzeiger-verlag.de/fileadmin/Fachverlag/Autorenservice/Handout_Abkuerzungen_Z-I_9.9.15.pdf

# Better is this:
# https://raw.githubusercontent.com/tsproisl/SoMaJo/master/somajo/abbreviations_de.txt

# I added: p.Erkl. Erkl. Zw.Fr. Zus.Fr. Frfr.
# Also: So.


import os


def mk_list_of_abbrevs():
    file_loc = './parli_data/'
    if not os.path.isdir(file_loc):
        file_loc = './'

    list_of_abbrevs = list()

    file_name = 'german_abbrevations.txt'
    file_ = file_loc + file_name

    with open(file_, 'r') as fin:
       abbrevs  = fin.read()

    for abbrv in abbrevs.split('\n'):
        abbrv = abbrv.strip()
        list_of_abbrevs.append(abbrv)

    list_of_abbrevs = list(filter(None, list_of_abbrevs))

    return list_of_abbrevs


if __name__ == '__main__':
    list_of_abbrevs = mk_list_of_abbrevs()
    print(*[abbr for abbr in list_of_abbrevs], end=' ')
