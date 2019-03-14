def _cities_as_last_names():
    with open('scraper_data/last_names_being_cities_too.txt', 'r') as fin:
        stadt_liste = fin.read()

    list_of_cities = list()

    for stadt in stadt_liste.split('\n'):
        stadt = stadt.strip()
        if stadt not in list_of_cities:
            list_of_cities.append(stadt)

    return list_of_cities


if __name__ == '__main__':
    list_of_cities = _cities_as_last_names()
    print(list_of_cities)
