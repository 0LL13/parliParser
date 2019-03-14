# Stopwords found here:
# https://raw.githubusercontent.com/solariz/german_stopwords/master/german_stopwords_full.txt

# Collection has been changed by me:
# - deleted all words that use 'ae' or 'oe' or 'ue' for umlauts 'ä', 'ö', and 'ü'
# - updated writing for 'ss' and 'ß'
# - kicked abbrevations, since that will be covered by a seperate list


import os


def mk_list_of_stopwords():
    file_loc = './parli_data/'
    if not os.path.isdir(file_loc):
        file_loc = './'

    list_of_stopwords = list()
    file_name = 'german_stopwords.txt'
    file_ = file_loc + file_name

    if not os.path.isfile(file_):
        raise Exception('File not found - check dir name or file name!')

    with open(file_, 'r') as fin:
       stopwords  = fin.read()

    for stopword in stopwords.split('\n'):
        stopword = stopword.strip()
        if stopword not in list_of_stopwords:
            list_of_stopwords.append(stopword)

    list_of_stopwords = list(filter(None, list_of_stopwords))

    return list_of_stopwords


if __name__ == '__main__':
    list_of_stopwords = mk_list_of_stopwords()
    print(list_of_stopwords[:25])
