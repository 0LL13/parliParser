def _low_cap_all(name):
    '''
    Subfunction _low_cap will capitalize the right parts of a compound familiy
    name. There are several versions:
        a)  Name1-Name2
        b)  Name1 Name2
        c)  von Name
        d)  Name1 zur Name2
        e)  auf der Name
        f)  Name1-von Name2
        ... and any other possible combinations

    Returns the standardized name with the right parts capitalized and parts
    like "von" or "zu" with lower letters only.
    '''
    connection_list = _make_list_of_connections(name)

    if connection_list:
        final_name = ''
        final_parts = _make_list_of_name_parts(name, connection_list)
        con_list = list(reversed(connection_list))
        for part in final_parts:
            try:
                final_name = final_name + _low_cap(part) + con_list.pop()
            except IndexError:
                final_name = final_name + _low_cap(part)
        return final_name
    else:
        return _low_cap(name)


def _make_list_of_connections(name):
    connection_list = list()
    final_name = ''
    for c in name:
        if c == '-':
            connection_list.append(c)
            hyphen_list = list()
        elif c == ' ':
            connection_list.append(c)
            space_list = list()
    return connection_list


def _make_list_of_name_parts(name, connection_list):
    parts = list()
    final_parts = list()
    for con in connection_list:
        if not parts:
            parts = [part for part in name.split(con)\
                    if len(name.split(con)) > 1]
        else:
            for part in parts:
                for item in part.split(con):
                    final_parts.append(item)
    if not final_parts:
        final_parts = parts

    return final_parts


def _low_cap(word):
    if word in ['ZUR', 'AUF', 'DER', 'VON', 'IN', 'VOM', 'DE', 'D']:
        return word.lower()
    else:
        return word.lower().capitalize()
