# List of German words found here:
# https://raw.githubusercontent.com/michmech/lemmatization-lists/master/lemmatization-de.txt
# and here is more:
# https://github.com/michmech/lemmatization-lists


import os
import sys


def mk_list_of_german_words():
    with open('parli_data/german_words.txt', 'r') as fin:
        words_ = fin.read()

    words = [word for word in words_.split('\n')]

    return list(words)


if __name__ == '__main__':
    l = mk_list_of_file()
    print(f'Number of entries: {len(l)}')
