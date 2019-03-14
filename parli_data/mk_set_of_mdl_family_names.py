import os
import sys


def mk_set_of_mdl_family_names():
    file_loc = './parli_data/'
    if not os.path.isdir(file_loc):
        file_loc = './'

    family_names = list()
    for wahlperiode in range(14, 17):
        file_name = f'Nachnamenliste_WP{wahlperiode}.txt'
        file_ = file_loc + file_name
        #print(file_)
        if not os.path.isfile(file_):
            raise Exception('File not found - check dir name or file name!')

        with open(file_, 'r') as fin:
            names = fin.read()

        new_names = [name for name in names.split('\n')]
        for name in new_names:
            name = name.strip()
            if name not in family_names:
                family_names.append(name)

    return family_names


if __name__ == '__main__':
    l = mk_set_of_mdl_family_names()
    for i, name in enumerate(l):
        print(i, name)
