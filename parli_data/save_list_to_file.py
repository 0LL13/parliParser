import sys


def _save_to_file():
    with open('./german_words.txt', 'r') as fin:
        words = fin.read()

    list_of_words = list()

    for i, line in enumerate(words.split('\n')):
        for word in line.split('\t'):
            word = word.strip()
            if word and word not in list_of_words:
                list_of_words.append(word)

    with open('./german_dict.txt', 'wt', encoding='utf-8') as fout:
        fout.write('\n'.join(word for word in list_of_words))

    return list_of_words


if __name__ == '__main__':
    import os
    file_loc = './german_dict.txt'
    if os.path.isfile(file_loc):
        with open(file_loc, 'r') as fin:
            words = fin.read()

        print([word for word in words.split('\n')])

    else:
        _save_to_file()
        #list_of_words = _mk_list_of_words()
