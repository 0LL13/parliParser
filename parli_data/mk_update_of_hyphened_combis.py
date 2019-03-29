import os
import sys


def mk_update_of_hyphened_combis():
    if os.path.isdir('./parli_data'):
        file_loc = './parli_data'
    else:
        file_loc = '.'
    file_ = f'{file_loc}/hyphened_combis.txt'
    file_new = f'{file_loc}/new_hyphened_combis.txt'

    if os.path.isfile(file_):
        with open(file_, 'r') as fin:
            hyphened_ = fin.read()

        hyphened_combis = [word for word in hyphened_.split('\n')]
        hyphened_combis = list(filter(None, hyphened_combis))
        hyphened_combis = set(hyphened_combis)
    else:
        raise Exception('File doesnt exist')

    if os.path.isfile(file_new):
        with open(file_new, 'r') as fin:
            new_ = fin.read()

        new_hyphened_combis = [word for word in new_.split('\n')]
        new_hyphened_combis = list(filter(None, new_hyphened_combis))
        new_hyphened_combis = set(new_hyphened_combis)
    else:
        raise Exception('File doesnt exist')

    hyphened_combis.update(new_hyphened_combis)

    with open(f'{file_loc}/hyphened_combis.txt', 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(hyphened_combis))

    with open(f'{file_loc}/new_hyphened_combis.txt', 'r+', encoding='utf-8') as fin:
        fin.truncate(0)

    print('Updated hyphened_combis and truncated new_hyphened_combis.')


if __name__ == '__main__':
    mk_update_of_hyphened_words()
