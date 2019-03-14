import os
import sys


def mk_list_of_hyphened_words():
    file_ = 'parli_data/hyphened_words.txt'

    with open(file_, 'r') as fin:
        hyphened_ = fin.read()

    hyphened_words = [word for word in hyphened_.split('\n')]

    return hyphened_words


if __name__ == '__main__':
    l = mk_list_of_hyphened_words()
    print(l)
