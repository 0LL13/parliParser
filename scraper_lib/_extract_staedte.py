def _make_list_of_cities():
    with open('parli_data/stadt_liste.txt', 'r') as fin:
        stadt_liste = fin.read()

    list_of_cities = list()

    for line in stadt_liste.split('\n'):
        if line.split(',')[-1] == 'Nordrhein-Westfalen':
            stadt = line.split(',')[1]
            if len(stadt.split(' ')) > 1:
                if stadt not in list_of_cities:
                    list_of_cities.append(stadt)
                if stadt.split(' ')[0] not in list_of_cities:
                    list_of_cities.append(stadt.split(' ')[0])
            else:
                if stadt not in list_of_cities:
                    list_of_cities.append(stadt)

    return list_of_cities


if __name__ == '__main__':
    list_of_cities = _make_list_of_cities(token=True)
    print(list_of_cities)
