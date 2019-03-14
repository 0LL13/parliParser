def ask_for_wahlperiode():
    wahlperiode_default = '14'
    wahlperiode = input('Welche Wahlperiode? ')
    if wahlperiode:
        return wahlperiode
    else:
        return wahlperiode_default


def ask_for_workflow():
    workflow = input('Welcher Workflow? (07, 10, 11, 18, 20)')
    if workflow:
        return workflow
    else:
        print('No workflow chosen, repeat ...')
        return ask_for_workflow()
