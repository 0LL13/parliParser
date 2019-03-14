import os
import sys


def mk_update_of_hyphened_words():
    if os.path.isdir('./parli_data'):
        file_loc = './parli_data'
    else:
        file_loc = '.'
    file_ = f'{file_loc}/hyphened_words.txt'
    file_new = f'{file_loc}/new_hyphened_words.txt'

    if os.path.isfile(file_):
        with open(file_, 'r') as fin:
            hyphened_ = fin.read()

        hyphened_words = [word for word in hyphened_.split('\n')]
        hyphened_words = list(filter(None, hyphened_words))
        hyphened_words = set(hyphened_words)
    else:
        raise Exception('File doesnt exist')

    if os.path.isfile(file_new):
        with open(file_new, 'r') as fin:
            new_ = fin.read()

        new_hyphened_words = [word for word in new_.split('\n')]
        new_hyphened_words = list(filter(None, new_hyphened_words))
        new_hyphened_words = set(new_hyphened_words)
    else:
        raise Exception('File doesnt exist')

    hyphened_words.update(new_hyphened_words)

    with open(f'{file_loc}/german_words.txt', 'r') as fin:
        words_ = fin.read()

    h_words = [word for word in words_.split('\n') if '-' in word]
    h_words = list(filter(None, h_words))
    h_words = set(h_words)
    nr_h_words = len(h_words)

    hyphened_words.update(new_hyphened_words)

    words_wo_hyphen = [word for word in words_.split('\n') if '-' not in word]
    words_wo_hyphen = list(filter(None, words_wo_hyphen))
    words_wo_hyphen = set(words_wo_hyphen)

    with open(f'{file_loc}/german_words.txt', 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(words_wo_hyphen))

    print(f'Updated german_words: moved {nr_h_words} words with hyphen out and saved file.')

    with open(f'{file_loc}/hyphened_words.txt', 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(hyphened_words))

    with open(f'{file_loc}/new_hyphened_words.txt', 'r+', encoding='utf-8') as fin:
        fin.truncate(0)

    print('Updated hyphened_words and truncated new_hyphened_words.')


if __name__ == '__main__':
    mk_update_of_hyphened_words()
