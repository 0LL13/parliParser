def _wer_regiert(wahlperiode='14'):
    '''
    subfunction _wer_regiert will return the string regPartei for the ruling
    party and a dict regKabinett to make it possible to connect a name that is
    only given with his office to a party.
    Returns: regPartei, regKabinett
    '''
    if wahlperiode == '17':
        regPartei = 'CDU'
        partyList = ['CDU', 'SPD', 'FDP', 'AfD', 'GRÜNE', 'FRAKTIONSLOS',\
                'FR. LOS']
        regKabinett = {'STAMP': 'FDP', 'LINIENKÄMPER': 'CDU',\
                'REUL': 'CDU', 'PINKWART': 'FDP', 'LAUMANN': 'CDU',\
                'GEBAUER': 'FDP', 'SCHARRENBACH': 'CDU', 'BIESENBACH': 'CDU',\
                'WÜST': 'CDU', 'SCHULZE FÖCKING': 'CDU',\
                'HOLTHOFF-PFÖRTNER': 'CDU',\
                'PFEIFFER-POENSGEN': 'FRAKTIONSLOS', 'KAISER': 'CDU'}
    elif wahlperiode == '16':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'GRÜNE', 'FDP', 'LINKE', 'PIRATEN',\
                'FRAKTIONSLOS']
        regKabinett = {'KRAFT': 'SPD', 'LÖHRMANN': 'GRÜNE',\
                'WALTER-BORJANS': 'SPD', 'DUIN': 'SPD', 'JÄGER': 'SPD',\
                'SCHNEIDER': 'SPD', 'SCHMELTZER': 'SPD', 'KUTSCHATY': 'SPD',\
                'REMMEL': 'GRÜNE', 'GROSCHEK': 'SPD', 'SCHULZE': 'SPD',\
                'SCHÄFER': 'SPD', 'KAMPMANN': 'SPD', 'STEFFENS': 'GRÜNE',\
                'SCHWALL-DÜREN': 'SPD', 'LERSCH-MENSE': 'SPD', \
                'GÖDECKE': 'SPD'}
    elif wahlperiode == '15':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'GRÜNE', 'FDP', 'LINKE', 'FRAKTIONSLOS']
        regKabinett = {'WALTER-BORJANS': 'SPD', 'VOIGTSBERGER': 'SPD',\
                'SCHULZE': 'SPD', 'SCHWALL-DÜREN': 'SPD', 'KUTSCHATY': 'SPD',\
                'SCHNEIDER': 'SPD', 'LÖHRMANN': 'GRÜNE', 'REMMEL': 'GRÜNE',\
                'STEFFENS': 'GRÜNE', 'KRAFT': 'SPD', 'JÄGER': 'SPD',\
                'SCHÄFER': 'SPD'}
    elif wahlperiode == '14':
        regPartei = 'CDU'
        partyList = ['CDU', 'SPD', 'GRÜNE', 'FDP', 'FRAKTIONSLOS']
        regKabinett = {'RÜTTGERS': 'CDU', 'KRAUTSCHEID': 'CDU',\
                'LASCHET': 'CDU', 'BREUER': 'CDU', 'LAUMANN': 'CDU',\
                'WITTKE': 'CDU', 'THOBEN': 'CDU', 'LIENENKÄMPER': 'CDU',\
                'LINSSEN': 'CDU', 'MÜLLER-PIEPENKÖTTER': 'CDU',\
                'SOMMER': 'CDU', 'PINKWART': 'FDP', 'WOLF': 'FDP',\
                'UHLENBERG': 'CDU'}
    elif wahlperiode == '13':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'GRÜNE', 'FDP', 'FRAKTIONSLOS']
        regKabinett = {'CLEMENT': 'SPD', 'SCHARTAU': 'SPD',\
                'SAMLAND': 'SPD', 'KRAFT': 'SPD', 'STEINBRÜCK': 'SPD',\
                'FISCHER': 'SPD', 'BEHRENS': 'SPD', 'DIECKMANN': 'SPD',\
                'BEHLER': 'SPD', 'VESPER': 'GRÜNE', 'KUSCHKE': 'SPD',\
                'HÖHN': 'GRÜNE', 'SCHWANHOLD': 'SPD', 'GERHARDS': 'SPD',
                'SCHÄFER': 'SPD', 'HORSTMANN': 'SPD'}
    elif wahlperiode == '12':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'GRÜNE']
        regKabinett = {'RAU': 'SPD', 'CLEMENT': 'SPD',\
                'DAMMEYER': 'SPD', 'HORSTMANN': 'SPD', 'BEHRENS': 'SPD',\
                'SCHLEUSSER': 'SPD', 'BEHRENS': 'SPD', 'BEHLER': 'SPD',\
                'RIDDER-MELCHERS': 'SPD', 'VESPER': 'GRÜNE', 'BRUSIS': 'SPD',\
                'KNIOLA': 'SPD', 'BRUNN': 'SPD', 'MÜNTEFERING': 'SPD',\
                'HÖHN': 'GRÜNE', 'FISCHER': 'SPD', 'HOMBACH': 'SPD',\
                'SCHLEUßER': 'SPD', 'DIECKMANN': 'SPD', 'KRUMSIEK': 'SPD',\
                'SCHNOOR': 'SPD', 'SCHWANHOLD': 'SPD', 'STEINBRÜCK': 'SPD'}
    elif wahlperiode == '11':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'FDP', 'DIE GRÜNEN', 'FRAKTIONSLOS']
        regKabinett = {'RAU': 'SPD', 'CLEMENT': 'SPD',\
                'SCHNOOR': 'SPD', 'HEINEMANN': 'SPD', 'EINERT': 'SPD',\
                'SCHLEUSSER': 'SPD', 'KRUMSIEK': 'SPD', 'SCHWIER': 'SPD',\
                'RIDDER-MELCHERS': 'SPD', 'MATTHIESEN': 'SPD',\
                'KNIOLA': 'SPD', 'BRUNN': 'SPD', 'MÜNTEFERING': 'SPD'}
    elif wahlperiode == '10':
        regPartei = 'SPD'
        partyList = ['CDU', 'SPD', 'F.D.P.']
        regKabinett = {'RAU': 'SPD', 'POSSER': 'SPD', 'SCHNOOR': 'SPD',\
                'HEINEMANN': 'SPD', 'EINERT': 'SPD', 'SCHLEUSSER': 'SPD',\
                'KRUMSIEK': 'SPD', 'SCHWIER': 'SPD', 'ZÖPEL': 'SPD',\
                'MATTHIESEN': 'SPD', 'JOCHIMSEN': 'SPD', 'BRUNN': 'SPD'}
    else:
        print('Wahlperiode not in range between 10 and 17!')
        return None, None

    return regPartei, regKabinett
