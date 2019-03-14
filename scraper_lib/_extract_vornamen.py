def _compare_vornamenListe():
    file_loc = './vornamen.txt'
    with open(file_loc,  'r') as fin:
        namensListe = fin.read()

    vornamenListe = list()
    for name in namensListe.split('\n'):
        if name:
            vornamenListe.append(name)

    print('my list got {} entries'.format(len(set(vornamenListe))))

    first_names = vornamenListe

    file_loc = './first_names.txt'
    with open(file_loc,  'r') as fin:
        namensListe = fin.read()

    vornamenListe = list()
    for name in namensListe.split('\n'):
        if name:
            vornamenListe.append(name.capitalize())

    print('other list got {} entries'.format(len(set(vornamenListe))))

    more_first_names = set(vornamenListe) - set(first_names)
    for name in more_first_names:
        print(name, end=' ')
    print(len(more_first_names))


def _get_vornamenListe():
    file_loc = './scraper_lib/vornamen.txt'
    with open(file_loc,  'r') as fin:
        namensListe = fin.read()

    vornamenListe = list()
    for name in namensListe.split('\n'):
        if name:
            vornamenListe.append(name)

    return vornamenListe


if __name__ == '__main__':
    #vornamenListe = _get_vornamenListe()
    #print(vornamenListe)
    _compare_vornamenListe()
