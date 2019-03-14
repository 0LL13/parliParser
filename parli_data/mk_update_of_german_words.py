# List of German words found here:
# https://raw.githubusercontent.com/michmech/lemmatization-lists/master/lemmatization-de.txt
# and here is more:
# https://github.com/michmech/lemmatization-lists


import os
import sys


def mk_update_of_german_words():
    if os.path.isdir('./parli_data'):
        file_loc = './parli_data'
    else:
        file_loc = '.'
    file_ = f'{file_loc}/german_words.txt'
    file_new = f'{file_loc}/new_german_words.txt'

    with open(f'{file_loc}/german_words.txt', 'r') as fin:
        words_ = fin.read()

    words = [word for word in words_.split('\n')]
    words = list(filter(None, words))
    words = set(words)
    print(f'Starting with {len(words)} words, partially lemmatized.')

    with open(f'{file_loc}/new_german_words.txt', 'r') as fin:
        new_ = fin.read()

    new_words = [word for word in new_.split('\n')]
    new_words = list(filter(None, new_words))
    new_words = set(new_words)
    print(f'Adding {len(new_words)} to dict.')

    words.update(new_words)
    print(f'Dict now with {len(words)} words.')

    with open(f'{file_loc}/german_words.txt', 'w', encoding='utf-8') as fout:
        fout.write('\n'.join(words))

    with open(f'{file_loc}/new_german_words.txt', 'r+') as fin:
        words_ = fin.read()
        fin.truncate(0)

    print('Updated german_words and truncated new_german_words.')


if __name__ == '__main__':
    mk_update_of_german_words()
