import copy
import datetime
import dill
import logging
import nltk
import os
import re
import sys

from collections import namedtuple
from collections import defaultdict
from nltk.tokenize import sent_tokenize
from operator import attrgetter
from pdf2textbox.pdf2textbox import _pdf_to_text_slice, _get_pdf_file
from parli_data.mk_set_of_german_abbrevations import mk_list_of_abbrevs
from parli_data.mk_set_of_german_abbrevations import\
                                        mk_list_of_abbrevs_followed_by_a_nr
from parli_data.mk_set_of_hyphened_words import mk_list_of_hyphened_words
from parli_data.mk_set_of_hyphened_combis import mk_list_of_hyphened_combis
from parli_data.mk_set_of_german_words import mk_list_of_german_words
from parli_data.mk_set_of_german_stopwords import mk_list_of_stopwords
from parli_data.mk_set_of_mdl_family_names import mk_set_of_mdl_family_names
from parli_data.mk_update_of_german_words import mk_update_of_german_words
from parli_data.mk_update_of_hyphened_words import mk_update_of_hyphened_words
from parli_data.mk_update_of_hyphened_combis import mk_update_of_hyphened_combis
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib.standardize_name import _low_cap_all


# see https://gist.github.com/zerolab/1633661 for smart double quotes
# ToDo: instead of ridding a word of "clutter" it would be more sensible to split
# it into a part that can be looked up in a dictionary and a second part that
# belongs to its context, like "quoted sentence!"
clutter = '[*!?,.;:_\s()\u201C\u201D\u201E\u201F\u2033\u2036\u0022]'

german_words = mk_list_of_german_words()
german_stopwords = mk_list_of_stopwords()
hyphened_words = mk_list_of_hyphened_words()
hyphened_combis = mk_list_of_hyphened_combis()


def wf15_convert_PDF2text_and_save():
    save = verbose = preview = legislature = False
    try:
        if sys.argv[1] == 's':
            save = True
        elif sys.argv[1] == 'v':
            verbose = True

        if sys.argv[2] in ['14', '15', '16']:
            legislature = sys.argv[2]
    except IndexError:
        verbose = True

    if not legislature:
        legislature = ask_for_wahlperiode()

    mk_update_of_german_words()
    mk_update_of_hyphened_words()
    mk_update_of_hyphened_combis()

    wp = _open_dilled_wp(legislature)
    base = f'./parli_data/wf11_sessions/WP{legislature}/'
    fn = wp.first_names
    fn.append('ECKHARD')            # missing!
    ln = wp.last_names

    for key, mdl in wp.MdLs.items():
        token = False
        if verbose:
            for protocol_nr, contribution in mdl.contributions.items():
                for start_end, contri in contribution.items():
                    _show_actual_contribution(mdl, legislature)
        elif save or preview:
            print(mdl.key)
            for k, v in mdl.speeches.collection.items():
                for kk, vv in v.items():
                    if kk == 'nr_of_speeches':
                        total = vv
            counter = 0
            for protocol_nr, start_end, sentences in _PDF_to_text(mdl, base, fn, ln):
                if preview:
                    if protocol_nr:
                        print(protocol_nr, start_end)
                        #for i, sent in enumerate(sentences):
                        #    print(i, sent)
                        check = input('Continue? ./n')
                        if check == 'n':
                            sys.exit()

                elif protocol_nr:
                    # printing with italics:
                    # https://indianpythonista.wordpress.com/2017/04/02/formatted-text-in-linux-terminal-using-python/
                    print('final text .............')
                    for i, sent in enumerate(sentences):
                        if sent.startswith('\u201E'):
                            print(i, '\x1b[3;37;46m' + sent + '\x1b[0m')
                        else:
                            print(i, sent)

                    #if '16903' in start_end: sys.exit()
                    #if '8345' in start_end: sys.exit()
                    #if '8019' in start_end: sys.exit()
                    #if '7679' in start_end: sys.exit()
                    #if '4783' in start_end: sys.exit()     # Apel-Haefs
                    #if '9532' in start_end: sys.exit()     # Apel-Haefs
                    #if '4711' in start_end: sys.exit()
                    #if '16836' in start_end: sys.exit()
                    #if '12715' in start_end: sys.exit()
                    #if '4172' in start_end: sys.exit()
                    #if '15755' in start_end: sys.exit()     # Asch
                    #if '14651' in start_end: sys.exit()     # Asch
                    #if '6799' in start_end: sys.exit()     # Asch
                    #if '4315' in start_end: sys.exit()     # Asch
                    #if '1507' in start_end: sys.exit()     # Asch
                    #if '14295' in start_end: sys.exit()     # Becker
                    #if '8019' in start_end: sys.exit()     # Becker
                    # I do not know how to correct the PDF blunder here: Becker, 4828
                    #if '4828' in start_end: sys.exit()     # Becker
                    #if '1031' in start_end: sys.exit()     # Becker
                    #if '393' in start_end: sys.exit()     # Becker
                    #if '17017' in start_end: sys.exit()     # Becker
                    #if '14379' in start_end: sys.exit()     # Becker
                    #if '10017' in start_end: sys.exit()     # Becker
                    #if '3404' in start_end: sys.exit()     # Becker
                    #if '2004' in start_end: sys.exit()     # Becker
                    #if '10248' in start_end: sys.exit()     # Becker
                    #if '10325' in start_end: sys.exit()     #Becker
                    #if '10316' in start_end: sys.exit()     #Becker
                    #if '87' in start_end: sys.exit()     # Becker
                    #if '14986' in start_end: sys.exit()     #Beer
                    #if '13641' in start_end: sys.exit()     #Beer
                    #if '13675' in start_end: sys.exit()     #Beer
                    #if '10441' in start_end: sys.exit()     #Beer
                    #if '7034' in start_end: sys.exit()
                    #if '5069' in start_end: sys.exit()

                    token = _save_the_contributions(legislature, key, protocol_nr,\
                            start_end, sentences, counter, total)
                else:
                    counter += 1

            if token:
                check = input('Continue? ./n')
                if check == 'n':
                    sys.exit()


def _show_actual_contribution(mdl, legislature):
    for protocol_nr, contribution in mdl.contributions.items():
        for start_end, contri in contribution.items():
            #if '8019' in start_end:
            #if '8014' in start_end:
            #if '7679' in start_end:
            #if '4711' in start_end:
            #if '12715' in start_end:
            #if '7927' in start_end:
            #if '4828' in start_end:
            #if '17017' in start_end:
            #if '9671' in start_end:
            #if '3404' in start_end:
            if '12518' in start_end:
                print('protocol_nr, start_end:', protocol_nr, start_end)
                print()
                kind = _get_kind_of_contribution(contri)
                start = start_end[0]
                end = start_end[-1]
                for k, sentences in contri.items():
                    if k != 'url':
                        if sentences != 'actual contribution':
                            print(start, end)
                            check = input('Show current contribution? y/.')
                            if check == 'y':
                                for i, sentence in enumerate(sentences):
                                    print(i+1, sentence)
                                print()
                            check = input('Reset current contribution? y/.')
                            if check == 'y':
                                _reset_contri(legislature, mdl.key, protocol_nr, start_end)
                        elif sentences == []:
                            check = input('Reset current contribution? y/.')
                            if check == 'y':
                                _reset_contri(legislature, mdl.key, protocol_nr, start_end)
                        else:
                            print('Nothing saved yet.')
                            print()
                    elif k == 'url':
                        url = contri['url']

                check = input('Continue? ./n')
                if check == 'n':
                    sys.exit()
                else:
                    print()
                    continue
    return None


def _PDF_to_text(mdl, base, first_names, last_names):
    mdl_names = mk_set_of_mdl_family_names()
    for protocol_nr in list(mdl.contributions):
        contribution = mdl.contributions[protocol_nr]
        for start_end in list(contribution):
            contri = contribution[start_end]
            kind = _get_kind_of_contribution(contri)
            start = start_end[0]
            end = start_end[-1]
            sentences = ''
            for k, v in contri.items():
                try:
                    url = contri['url']
                except KeyError:
                    files = os.listdir(base)
                    for fyle in files:
                        fyle_start = int(fyle.split('|')[-2])
                        fyle_end = int(fyle.split('|')[-1].split('.')[0])
                        start = int(start)
                        if fyle_start <= start <= fyle_end:
                            print('fyle', fyle)
                            url = fyle.split('.')[0]
                            start = str(fyle_start)
                            end = str(fyle_end)
                            break
                    if not url:
                        print(f'start: {start}, end: {end}')
                        print('contri', contri)
                        raise Exception('No file found to match contri, _PDF_to_text')
                if k != 'url' and (v == 'actual contribution' or v == []):
                    pdf_loc = base + url + '.pdf'
                    pdf = _get_pdf_file(pdf_loc, verbose=False)
                    dict_of_boxes = _pdf_to_text_slice(pdf, start, end, verbose=False)
                    #for k, v in dict_of_boxes.items():
                    #    print(v)
                    #sys.exit()
                    boxes = _speech_converter(dict_of_boxes, mdl, first_names,\
                            last_names, kind, start, end)
                    #_print_current_results(boxes)
                    if boxes == []:
                        continue
                    box_list = _mk_list_of_boxes(boxes, start, end)
                    #_print_current_results(box_list)
                    sentences = _mk_plain_text(box_list, mdl, mdl_names, start, end)
                    #_print_current_results(sentences)
                    yield protocol_nr, start_end, sentences

                elif k != 'url' and v != 'actual contribution':
                    print('.', end='')
                    yield None, None, None


def _mk_plain_text(boxes, mdl, mdl_names, start, end):
    boxes = _get_rid_of_remarks_within_box(boxes)
    #_print_current_results(boxes)
    boxes = _get_rid_of_name(boxes, mdl, start, end)
    #_print_current_results(boxes)
    complete_text = _connect_boxes(boxes, german_words, mdl_names)
    #_print_current_results(complete_text)
    sentences = nltk.sent_tokenize(complete_text, language='german')
    sentences =  _get_rid_of_line_breaks_wth_hyphens(sentences, mdl_names)
    sentences = _get_rid_of_line_breaks(sentences)
    sentences = _find_words_sep_by_hyphens(sentences, mdl_names)
    sentences =  _find_words_sep_by_hyphens_within_sentence(sentences, mdl_names)
    sentences = _find_last_remarks(sentences)
    #_print_current_results(sentences)
    sentences = _connect_sentences(sentences)
    sentences = _connect_dates(sentences)
    sentences = _consider_quotes(sentences)

    return sentences


def _print_current_results(results):
    print()
    for i, item in enumerate(results):
        print(i, item)
    sys.exit()


def _mk_list_of_boxes(boxes, start, end, name=None):
    '''
    Does two things: basically taking the box.text part of those boxes and appending
    them in a list.
    However, now is the only chance to find isolated text snippets that got lost
    during PDF to text conversion - I call this "PDF blunder".
    --> will try to put it at the right place and ask for forgiveness. If wrong,
    too bad.

    Open question: What if the text fragments that got lost are longer than one line?
                   --> If a fragment has more than 40 characters I'll treat it as an
                       error with no consequences (no exception will be raised)
    Open question: What if the same word gets lost twice?
    Open question: What if two words have the same extension?

    Returns a list with texts as found in boxes coming from pdf2textbox
    '''
    func_name = '_mk_list_of_boxes starting here'
    #_self_intro(func_name, name)
    #_print_current_results(boxes)
    box_list = list()
    sep_boxes_before = list()
    sep_boxes_after = list()
    words = new_text = ''
    nr_of_sep_boxes_before = 0       # tells how many boxes to take out of box_list
    nr_of_sep_boxes_after = 0        # tells how many boxes to skip later on
    for i, box in enumerate(boxes):
        index = i
        if nr_of_sep_boxes_after > 0:
            #print('nr_of_sep_boxes_after > 0, snipping this box:')
            nr_of_sep_boxes_after -= 1
            continue
        #print(index, box)
        #print('nr_of_sep_boxes_after:', nr_of_sep_boxes_after)
        false_alarm = True
        too_many_lines = _could_be_box_w_missing_text(box, start, end)
        lines_too_short = _could_be_lines_too_short(box)
        if too_many_lines or lines_too_short:
            _show_box_that_could_miss_some_text(box, too_many_lines, lines_too_short)
        if too_many_lines:
            box_list, false_alarm, nr_of_sep_boxes_after =\
                    _correct_boxlist(i, boxes, box_list, false_alarm, start, end)
            if false_alarm:
                box_list = _add_to_box_list(box.text, start, end, box_list)
                continue
        if lines_too_short:
            lines = box.text.split('\n')
            for j, line in enumerate(lines):
                print(j, line)
            try:
                box_before = boxes[index-1]
            except IndexError:
                box_before = None
            if box_before and _nr_of_lines_equals_one(box_before):
                box_list = _add_boxes_from_before(index, box_before, boxes,\
                        box_list, start, end)
                continue
            try:
                next_box = boxes[index+1]
            except IndexError:
                # if neither before nor after the box in question is a candidate to
                # fill the void it's no use to continue --> add box and continue
                if not box_before:
                    box_list = _add_to_box_list(box.text, start, end, box_list)
                break
            if next_box and _nr_of_lines_equals_one(next_box):
                print('a')
                box_list, nr_of_sep_boxes_after = _add_boxes_from_next(index,\
                        next_box, boxes, box_list, start, end)
                continue
            else:
                box_list = _add_to_box_list(box.text, start, end, box_list)
                continue
        box_list = _add_to_box_list(box.text, start, end, box_list)

    #print()
    #print('box_list in _mk_list_of_boxes')
    #for i, box in enumerate(box_list):
    #    print(i, box)
    #sys.exit()

    return box_list


def _add_boxes_from_before(index, box_before, boxes, box_list, start, end):
    print('box_before', box_before)
    box = boxes[index]
    sep_boxes = list()
    sep_boxes.append(box_before)
    index = index-1
    counter = 1
    while True:
        try:
            index -= 1
            box_before = boxes[index]
            if _nr_of_lines_equals_one(box_before):
                sep_boxes.append(box_before)
                counter += 1
            else:
                break
        except IndexError:
            break
    box_coords = _get_coords(box)
    #print(sep_boxes)
    new_text, nr_of_gaps = \
            _mk_text_great_again(sep_boxes, box_coords, box, after=True)
    if new_text:
        box_list = box_list[:-counter]
        box_list = _add_to_box_list(new_text, start, end, box_list)
    else:
        box_list = _add_to_box_list(box.text, start, end, box_list)

    return box_list


def _add_boxes_from_next(index, next_box, boxes, box_list, start, end):
    box = boxes[index]
    sep_boxes = list()
    sep_boxes.append(next_box)
    index = index+1
    nr_of_sep_boxes_after = 1
    while True:
        try:
            index += 1
            next_box = boxes[index]
            if _nr_of_lines_equals_one(next_box):
                sep_boxes.append(next_box)
                nr_of_sep_boxes_after += 1
            else:
                break
        except IndexError:
            break
    box_coords = _get_coords(box)
    #print(sep_boxes)
    new_text, nr_of_gaps = \
            _mk_text_great_again(sep_boxes, box_coords, box, after=True)
    if new_text:
        box_list = _add_to_box_list(new_text, start, end, box_list)
    else:
        box_list = _add_to_box_list(box.text, start, end, box_list)

    return box_list, nr_of_sep_boxes_after


def _show_box_that_could_miss_some_text(box, too_many_lines, lines_too_short):
    print(f'too_many_lines: {too_many_lines}')
    print(f'lines_too_short: {lines_too_short}')
    #lines = box.text.split('\n')
    #for index, line in enumerate(lines):
    #    print(index, line, len(line))


def _correct_boxlist(i, boxes, box_list, false_alarm, start, end):
    #print()
    #print('_correct_boxlist starting here')
    #print('box_list on entry:')
    #print(box_list)
    box = boxes[i]
    new_text = list()
    box_coords = _get_coords(box)
    sep_boxes_before = _find_sep_boxes(i, boxes, box_coords, before=True)
    sep_boxes_after = _find_sep_boxes(i, boxes, box_coords, after=True)
    if len(sep_boxes_before) > 0:
        false_alarm = False
        #print('found sep_boxes before:')
        #print(sep_boxes_before)
        #print()
        #print('current box_list:')
        #for box_nr, box_text in enumerate(box_list):
        #    print(box_nr, box_text)
        new_text, nr_of_sep_boxes_before =\
                _mk_text_great_again(sep_boxes_before, box_coords, box, before=True)
        index= len(box_list)
        boxes_to_snip = index - nr_of_sep_boxes_before
        nr_of_sep_boxes_before = 0
        box_list = box_list[:boxes_to_snip]
        box_list = _add_to_box_list(new_text, start, end, box_list)
        #print()
        #print('box_list after snipping the sep_box:')
        #for box_nr, box_text in enumerate(box_list):
        #    print(box_nr, box_text)
    if len(sep_boxes_after) > 0:
        false_alarm = False
        #print('found sep_boxes after')
        #print(sep_boxes_after)
        new_text, nr_of_sep_boxes_after =\
                _mk_text_great_again(sep_boxes_after, box_coords, box,\
                after=True, new_text=new_text)
        box_list = _add_to_box_list(new_text, start, end, box_list)

    #print()
    #print('box_list on exit:')
    #print(box_list)
    return box_list, false_alarm, len(sep_boxes_after)


def _add_to_box_list(new_text, start, end, box_list):
    #print()
    #print('_add_to_box_list starting here')
    #print(new_text)
    words = _prepare_text(new_text, start, end, name='_add_to_box_list')
    #print(words)
    if not words or words == []:
        pass
    else:
        text = ' '.join(w for w in words)
        box_list.append([text])

    return box_list


def _mk_text_great_again(sep_boxes, box_coords, box, before=False, after=False,\
        new_text=list(), name=None):
    '''
    The problem I'm facing here is that I need to tell the function that calls
    this one how many sep_boxes actually turned out to be accepted for correction.
    Not all will, that much is sure, but how do I count this?

    Returns a list with corrected text and the number of gaps
    '''
    func_name = '_mk_text_great_again'
    #_self_intro(func_name, name)
    before = before
    after = after
    #print(f'before: {before}, after: {after}')
    nr_of_gaps = 0
    new_text = new_text
    corrected_text = new_text
    oddies = _find_oddies(sep_boxes, box_coords, before, after, name=func_name)
    #print(oddies)
    gaps = _mk_dict_of_gaps_in_lines(oddies, box_coords)
    #print('gaps', gaps)
    for k, v in gaps.items():
        for _, vv in v.items():
            for kee in vv.keys():
                if kee == 'oddy':
                    nr_of_gaps += 1
    for _, gap_dict in gaps.items():
        #print('gap_dict', gap_dict)
        gaps, new_text = _fill_gaps(gaps, box, new_text)
        corrected_text = _correct_line(gaps, new_text)

    #for index, line in enumerate(new_text):
    #    print(index, line)
    #print(new_text)
    #sys.exit()

    #print('gaps', gaps)
    return corrected_text, nr_of_gaps


def _correct_line(gaps, new_text):
    #print()
    #print('_correct_line starting here')
    #print('gaps', gaps)
    #print('new_text', new_text)
    d = gaps
    best_fits = list()
    correct_line = list()
    corrected_line = ''
    for k, v in d.items():
        #print('k, v in gaps.items()')
        #print(k, v)
        for kk, vv in v.items():
            #print('vv.keys()', vv.keys())
            try:
                best_fits = sorted([bf for bf in vv.keys() if bf != 'oddy' and bf > 0])
                #print('best_fits', best_fits)
            except (AttributeError, TypeError):
                pass
            if best_fits == []:
                continue
            else:
                for bf in best_fits:
                    #print('bf, vv[bf]', bf, vv[bf])
                    if vv[bf] in correct_line:
                        continue
                    elif vv[bf][-1] == '-' and vv[bf][-2] != ' ':
                        #print('connecting hyphen')
                        #print(vv[bf])
                        try:
                            if vv['oddy'][0].isupper():
                                correct_line.append(vv['oddy'])
                                correct_line.append(vv[bf])
                        except IndexError:
                            correct_line.append(vv[bf])
                    elif vv[bf][-1] == '-' and vv[bf][-2] == ' ':
                        #print('seperating hyphen')
                        #print(vv[bf])
                        try:
                            correct_line.append(vv[bf])
                            correct_line.append(vv['oddy'])
                        except IndexError:
                            correct_line.append(vv[bf])
                    else:
                        correct_line.append(vv[bf])
                        if vv['oddy']:
                            correct_line.append(vv['oddy'])
                        break
                corrected_line = ' '.join(part for part in correct_line)
                for i, line in enumerate(new_text):
                    if line == vv[bf]:
                        new_text[i] = corrected_line
    #print()
    #print('new_text with corrected line:')
    #for index, line in enumerate(new_text):
    #    print(index, line)
    #sys.exit()

    return new_text


def _could_be_box_w_missing_text(box, start, end):
    '''
    This is a new try to eventually skip the part where I have to manually check if
    a piece of text is or is not where it should be - it's just to many incidences
    and I want to automate this.
    1. Count units of y-axis: y_extension
       --> there should be y_extension / 11.8 number of lines:
           nr_of_lines_to_expect = y_extension / 11.8
    2. Number of lines: split by "\n"
       --> nr_of_lines_in_fact = len(box.text.split('\n'))
       --> if nr_of_lines_in_fact > nr_of_lines_to_expect:
           --> this is a box where a PDF-blunder could have occured
           --> return True

    '''
    y_extension = box.y1 - box.y0
    nr_of_lines_to_expect = round(y_extension/11.8)
    text = box.text
    text_split_in_lines = text.split('\n')
    text_split_in_lines = list(filter(None, text_split_in_lines))
    nr_of_lines_in_fact = len(text_split_in_lines)
    #print('nr_of_lines_to_expect', nr_of_lines_to_expect, y_extension)
    #print('nr_of_lines_in_fact', nr_of_lines_in_fact)

    if nr_of_lines_in_fact != nr_of_lines_to_expect:
        #print('Found box where text could be missing:')
        #print(box)
        #print('nr of lines do not match, text.split("\\n"):')
        #for i, line in enumerate(text_split_in_lines):
        #    print(i, line, len(line))
        return True
    return False


def _could_be_lines_too_short(box):
    '''
    To find PDF blunders sometimes a look at a block of text can highlight lines
    with less than 40 characters and no period or other sentence-finishing mark at
    its end. These lines are potential candidates to insert text fragments that
    PDF has taken out of context and inserted someplace else.

    Will check if there are more than one line. If not, it doesn't make sense to
    call this line a line that is too short and returns False.

    If there are more than one line and one of them has less than 40 characters:
    returns True.
    '''
    quotes = ['\u201C', '\u201D', '\u201E', '\u201F', '\u2033', '\u2036', '\u0022']
    puncts = ['.', '!', '?', ':', '-', ')']
    header_shmutz = ['Landtag', 'Nordrhein-Westfalen', 'Plenarprotokoll']
    text = box.text
    text_split_in_lines = text.split('\n')
    text_split_in_lines = list(filter(None, text_split_in_lines))
    nr_of_lines = len(text_split_in_lines)
    if nr_of_lines < 2:
        return False

    for i, line in enumerate(text_split_in_lines):
        line = line.strip()
        if not line:
            continue
        length = len(line)
        #print(i, line, length)
        if length < 40:
            if line[-1] in quotes:
                line = line[:-1]
            if line[-1] in puncts:
                continue
            if line in header_shmutz:
                continue
            else:
                #print('This line shorter than 40 chars: ', line)
                return True
    return False


def _nr_of_lines_equals_one(box):
    '''
    If a remark pattern is found, the function returns False since this line will be
    skipped anyway.
    Returns bool(True or False)
    '''
    text = box.text
    remark_pattern = re.compile('\((Beifall|Zuruf).*\)')
    m = re.search(remark_pattern, text)
    if m:
        return False
    text_split_in_lines = text.split('\n')
    text_split_in_lines = list(filter(None, text_split_in_lines))
    nr_of_lines = len(text_split_in_lines)
    if nr_of_lines == 1:
        return True
    else:
        return False


def _get_coords(box):
    x0 = box.x0
    x1 = box.x1
    y0 = box.y0
    y1 = box.y1
    box_coords = (x0, x1, y0, y1)
    return box_coords


def _find_sep_boxes(i, boxes, box_coords, before=False, after=False):
    '''
    So, now I found a box that seems to have lost at least one word, which got
    delivered within a seperate box. Not good.
    Go in one direction: either boxes before or boxes after the box in question.
    Continue as long a box fits into the box in question, quit at first incident
    that box does not fit in.
    Obviously this only works inside a single column. If stuff from the left column
    got into the right and vice versa it will be lost. And me, too.

    '''
    #print()
    #print('_find_sep_boxes starting here')
    #print(f'before: {before}, after: {after}, box-index i: {i}')
    assert before or after
    box = boxes[i]
    sep_boxes = list()

    if after:
        boxes_after = boxes[i+1:]
        boxes_to_check = boxes_after
        if boxes_to_check == []:
            return sep_boxes        # would it be worth checking the box after??
    elif before:
        if i == 0:
            return sep_boxes        # because there are no boxes before boxes[0]
        boxes_before = list(reversed(boxes[:i]))
        boxes_to_check = boxes_before

    token = True
    #print('boxes_to_check:')
    #print(boxes_to_check)
    counter = 0
    max = len(boxes_to_check)

    while token:
        for b_o_x in boxes_to_check:
            counter += 1
            b_o_x_coords = _get_coords (b_o_x)
            #print('box_coords (big)', box_coords)
            #print('b_o_x_coords (small)', b_o_x_coords)
            if _is_inside_of_box(box_coords, b_o_x_coords):
                sep_boxes.append(b_o_x)
                if counter >= max:
                    token = False
                    break
            else:
                token = False
                break
    #if after:
    #    print(sep_boxes)
    #    sys.exit()
    return sep_boxes


def _find_oddies(sep_boxes, box_coords, before=False, after=False, name=None):
    func_name = '_find_oddies'
    #print()
    #print(f'{func_name} starting here', end=' ')
    #if name:
    #    print(f'called by {name}')
    #else:
    #    print()
    assert before or after
    #print(f'before: {before}, after: {after}')
    x0, x1, y0, y1 = box_coords
    y_extension = y1 - y0
    nr_of_lines_to_expect = round(y_extension/11.8)
    oddies = dict()
    for j, sep_box in enumerate(sep_boxes):
        print('sep_box', sep_box)
        #print('j, sep_box', j, sep_box)
        c = round((sep_box.x0 - x0) / 4.9)
        for index in range(nr_of_lines_to_expect):
            if before:
                line_nr = index
            else:
                line_nr = nr_of_lines_to_expect - index
            #print(line_nr, sep_box.y0, round(y0 + (index+0.4)*11.8), sep_box.y1)
            if sep_box.y0 <= round(y0 + (index+0.4)*11.8) <= sep_box.y1:
                try:
                    oddies[line_nr].append(sep_box)
                except KeyError:
                    oddies[line_nr] = list()
                    oddies[line_nr].append(sep_box)
                break
    #print(oddies)
    #sys.exit()
    return oddies


def _mk_dict_of_gaps_in_lines(oddies, box_coords, name=None):
    '''
    This function takes the fragmented text pieces that were found in "oddies"
    and calculates the gap that exists in front of the lost text fragment (or
    after if there is more than one "oddy").
    At this point I have not found out yet where this fragmented piece will have
    to be placed. So all I do is calculate the space that according to its
    PDF coordinates is in front of it or after it.

    Result looks like this:
        gap:{'oddy': text of lost box}
    With gap being the space between the box frame and the start of the lost box.
    '''
    func_name = '_mk_dict_of_gaps_in_lines'
    #_self_intro(func_name, name)
    s = [(k, oddies[k]) for k in sorted(oddies, key=oddies.get)]
    #print('s', s)
    gaps = dict()
    for k, v in s:
        gaps[k] = dict()
        lost_boxes = [box for box in sorted(v, key=attrgetter('x0'))]
        #print('lost_boxes', lost_boxes)
        for i, lost_box in enumerate(lost_boxes):
            lost_text = lost_box.text.strip()
            #print('lost_text', i, lost_text)
            if i == 0:
                gap = lost_box.x0 - box_coords[0]
                #print('i == 0')
                #print('gap, x0, box_coords', gap, lost_box.x0, box_coords)
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
            elif i > 0 and i == len(lost_boxes)-1:
                gap = lost_box.x0 - lost_boxes[i-1].x1
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
                gap = box_coords[1] - lost_box.x1
            else:
                gap = lost_box.x0 - lost_boxes[i-1].x1
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
        # Filtering with ext > 17 is based on the assumption that in German a word
        # must have two characters (like "zu", "an", "da") plus a space before and
        # after, which means 4*4.9 = 19.6 --> must be 18 at least
        gaps_keys = [kee for kee in gaps[k].keys()]
        #print('gaps_keys', gaps_keys)
        #print('k, gaps[k]', k, gaps[k])
        kee = -1
        for i, gap in enumerate(gaps_keys):
            if gap <= 17:
                if kee < 0:
                    kee = gaps_keys[i-1]
                try:
                    #print('k, gap, gaps[k]', k, gap, gaps[k])
                    #print('gaps[k][kee]', gaps[k][kee])
                    #print('gaps[k][gap]', gaps[k][gap])
                    #print('gaps[k][kee]["oddy"]', gaps[k][kee]["oddy"])
                    #print('gaps[k][gap]["oddy"]', gaps[k][gap]["oddy"])
                    gaps[k][kee]['oddy'] += ' ' + gaps[k][gap]['oddy']
                    #print('gaps[k][kee]["oddy"]', gaps[k][kee]["oddy"])
                except KeyError:
                    pass

                del gaps[k][gap]['oddy']
                del gaps[k][gap]
            else:
                kee = -1

    #print(f'gaps in {func_name}')
    #print(gaps)
    #sys.exit()
    return gaps


def _self_intro(func_name, name):
    print()
    print(f'{func_name} starting here', end=' ')
    if name:
        print('called by {name}')
    else:
        print()

    return None


def _is_inside_of_box(box_coords_big, box_coords_small):
    x0, x1, y0, y1 = box_coords_big
    x_0, x_1, y_0, y_1 = box_coords_small

    if x0 <= x_0 and x_1 <= x1:
        if y0 <= y_0 and y_1 <= y1:
            return True

    return False


def _fill_gaps(gaps, box, new_text):
    '''
    After finding the gaps that the lost text fragments create within the line they
    occupy this function looks for words of the "big box" (which was called out as
    having a line or more missing) that could fit into those gaps.
    This assumes that the words of the big box are not necessarily in the right
    order and that the coordinates of the fragment is right! I have seen that in
    wp14, Horst Becker, 11167. Not sure if it cannot also be the other way round ...

    Returned is a dict that for each line offers one or more words to fill the gap
    before the "oddy" and the oddy itself.
    '''
    #print()
    #print('_fill_gaps starting here')
    quotes = ['\u201C', '\u201D', '\u201E', '\u201F', '\u2033', '\u2036', '\u0022']
    header_shmutz = ['Landtag', 'Nordrhein-Westfalen', 'Plenarprotokoll']
    # puncts are sentence FINISHERS! It must be possible to have a new paragraph next.
    puncts = ['.', '!', '?']
    #print('new_text:', [new_text])
    if new_text == [] or new_text == None or new_text == '':
        #print('new_text == []')
        box_text = box.text.split('\n')
        box_text = list(filter(None, box_text))
        new_text = list()
    else:
        box_text = new_text
        new_text = list()
    line_nr = 0
    #print('new_text:', new_text)
    #print('box_text')
    #print(box_text)

    for i, line in enumerate(box_text):
        line = line.strip()
        line_nr = i+1
        #print('line_nr (=index+1), line:', line_nr, line)
        if not line:
            continue
        elif line in header_shmutz:
            continue
        elif len(line) >= 40:
            new_text.append(line)
            line_nr += 1
        elif line[-1] in puncts:
            new_text.append(line)
            line_nr += 1
        elif line[-1] in quotes:
            if line[-2] in puncts:
                new_text.append(line)
                line_nr += 1
        else:
            # even if this line will not be the right candidate for filling the gap
            # it will be added to the list "new_text"
            new_text.append(line)
            line_nr += 1
            fragm_extension = round(len(line)*4.9)
            for lineNr, v in gaps.items():
                #print('filling gaps for line_nr, line:', line_nr, line)
                for gap, vv in v.items():
                    try:
                        #print('gap, vv', gap, vv)
                        leftover = gap - fragm_extension
                        #print('leftover, line', leftover, line)
                        if leftover < 3:
                            continue
                        vv[leftover] = line
                    except TypeError:
                        pass

    #print('gaps in _fill_gaps', gaps)
    #print('new_text:')
    #for index, line in enumerate(new_text):
    #    print(index, line)
    #sys.exit()
    return gaps, new_text


def _connect_sentences(sentences):
    '''
    Will connect two sentences, if the last word of the first sentence is an
    abbreviation.
    Will fail if the abbreviation is also the end of the sentence! In this case
    it will connect two sentences. This is not intended but I do not know how to
    find out if an abbreviation is also the end of the sentence.
    '''
    abbrevs = mk_list_of_abbrevs()
    abbrevs_followed_by_a_nr = mk_list_of_abbrevs_followed_by_a_nr()
    exceptions = ['sen.', 'So.', 'gel.']
    #for exc in exceptions:
    #    abbrevs.remove(exc)
    new_sentences = list()
    skip = False
    for i, sentence in enumerate(sentences):
        if not skip:
            new_sentence = ''
        else:
            skip = False
            continue
        try:
            next_sent = sentences[i+1]
        except IndexError:
            new_sentences.append(sentence)
            continue

        words = sentence.split(' ')
        words = list(filter(None, words))
        last_word = words[-1].strip()
        next_words = next_sent.split(' ')
        first_word = next_words[0].strip()
        try:
            next_first_word = next_words[1].strip()
        except IndexError:
            next_first_word = ''
        new_word = last_word + first_word   # i.e. last_w: z., first_w: B. --> z.B.
        if last_word in abbrevs:
            if words[-2].strip().endswith('-'):
                print(words)
                raise Exception('_connect_sentences')
                new_sentence += sentence
                new_sentence = re.sub(' +', ' ', new_sentence)
                new_sentences.append(new_sentence)
            elif last_word in abbrevs_followed_by_a_nr:
                if next_first_word.isdigit():
                    new_sentence += sentence + ' ' + next_sent
                    new_sentence = re.sub(' +', ' ', new_sentence)
                    new_sentences.append(new_sentence)
                    skip = True
                else:
                    new_sentence += sentence
                    new_sentence = re.sub(' +', ' ', new_sentence)
                    new_sentences.append(new_sentence)
            elif next_first_word in abbrevs:
                # sentence needs to continue without empty space
                print('next_first_word in abbrevs')
                print(words)
                print(next_words)
                #sys.exit()
                new_sentence += sentence + next_sent
                new_sentence = re.sub(' +', ' ', new_sentence)
                skip = True
            else:
                new_sentence += sentence + ' ' + next_sent
                new_sentence = re.sub(' +', ' ', new_sentence)
                new_sentences.append(new_sentence)
                skip = True
            print('After finding an abbreviation at the end of a sentence:')
            print(new_sentence)
            print('abbreviation:', last_word)
        elif new_word in abbrevs:
            new_words = words[:-1] + [new_word] + next_words[1:]
            new_sentence += ' '.join(w for w in new_words)
            new_sentence = re.sub(' +', ' ', new_sentence)
            new_sentences.append(new_sentence)
            skip = True
        else:
            new_sentence += sentence
            new_sentence = re.sub(' +', ' ', new_sentence)
            new_sentences.append(new_sentence)

    return new_sentences


def _connect_dates(sentences):
    '''
    Will connect two sentences, if the last word of the first sentence is an digit
    and the first word in the sentence after is a month.
    '''
    new_sentences = list()
    skip = False
    months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August',\
            'September', 'Oktober', 'November', 'Dezember', 'Jan.', 'Feb.', 'Aug.',\
            'Sept.', 'Okt.', 'Nov.', 'Dez.']
    for i, sentence in enumerate(sentences):
        if not skip:
            new_sentence = ''
        else:
            skip = False
            continue
        try:
            next_sent = sentences[i+1]
        except IndexError:
            new_sentences.append(sentence)
            continue

        words = sentence.split(' ')
        words = list(filter(None, words))
        last_word = words[-1].strip()
        if last_word[-2].isdigit():
            next_words = next_sent.split(' ')
            first_word = next_words[0].strip()
            if first_word in months:
                new_sentence = sentence + ' ' + next_sent
                new_sentences.append(new_sentence)
                skip = True
        else:
            new_sentences.append(sentence)

    return new_sentences


def _save_the_contributions(legislature, key, protocol_nr, start_end,\
        sentences, counter, total):
    wp = _open_dilled_wp(legislature)
    token = False
    for _, mdl in wp.MdLs.items():
        if mdl.key == key:
            contri = mdl.contributions[protocol_nr][start_end]
            for k, v in contri.items():
                if k != 'url':
                    if v == 'actual contribution':
                        contri[k] = sentences
                        token = True
                        break
                    elif v == []:
                        check = input('Reset current contribution? y/.')
                        if check == 'y':
                            _reset_contri(legislature, mdl.key, protocol_nr, start_end)
                    else:
                        print('.', end='')
                        break

    if token:
        print(f'Transferred {counter} of {total} contributions from PDF to text.')
        dir_loc = f'/home/frodo/Python-Projekte/parli_NRW/parli_NRW/data/WP{legislature}/'
        dir_local = './parli_data/wf15_dilled_wps/'
        os.makedirs(dir_loc, exist_ok=True)

        ln = key.split('_')[0].lower()
        fn = key.split('_')[1].split(' ')[0]
        fn = fn.strip().lower()
        file_loc = dir_loc + f'{ln}_{fn}.dill'
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        file_local = dir_local + 'WP_{}.dill'.format(legislature)
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        print(f'Saved contribution {k} at position {start_end}')
        return True
    return False


def _reset_contri(legislature, key, protocol_nr, start_end):
    wp = _open_dilled_wp(legislature)
    token = False
    for _, mdl in wp.MdLs.items():
        if mdl.key == key:
            contri = mdl.contributions[protocol_nr][start_end]
            for k, v in contri.items():
                if k != 'url':
                    contri[k] = 'actual contribution'
                    token = True
                    break

    if token:
        dir_loc = f'/home/frodo/Python-Projekte/parli_NRW/parli_NRW/data/WP{legislature}/'
        dir_local = './parli_data/wf15_dilled_wps/'
        os.makedirs(dir_loc, exist_ok=True)

        ln = key.split('_')[0].lower()
        fn = key.split('_')[1].split(' ')[0]
        fn = fn.strip().lower()
        file_loc = dir_loc + f'{ln}_{fn}.dill'
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        file_local = dir_local + 'WP_{}.dill'.format(legislature)
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        print(f'Reset of contribution {k} at position {start_end}')
        return True
    return False


def _find_a_single_contribution():
    legislature = ask_for_wahlperiode()
    wp = _open_dilled_wp(legislature)
    base = f'./parli_data/wf11_sessions/WP{legislature}/'
    first_names = wp.first_names
    last_names = wp.last_names

    protocolNr = input('Which protocol_nr?\n')

    for _, mdl in wp.MdLs.items():
        for protocol_nr, contribution in mdl.contributions.items():
            if protocol_nr == protocolNr:
                print(mdl.key)
                print(contribution)
                sys.exit()


def _get_kind_of_contribution(contri):
    for k in contri.keys():
        if '_' in k:
            kind = k.split('_')[0]
            break
        else:
            kind = 'speech'

    return kind


def _remove_linebreaks(boxes):
    box_list = list()
    for box in boxes:
        for word in box.split(' '):
            new_word = word.strip('\n')
            text = ' '.join(new_word)

    return text


def _is_url_or_mail_address(word):
    # using regex
    # from stackoverflow: https://stackoverflow.com/a/8234912/6597765

    word_without_clutter = re.sub(clutter, '', word)
    urlRegex = re.compile(r'^(\[[A-z0-9 _]*\]\()?((?:(http|https):\/\/)?(?:[\w-]+\.)+[a-z]{2,6})(\))?$')
    if urlRegex.search(word_without_clutter):
        return True
    return False


def _speech_converter(boxes, mdl, first_names, last_names, kind, start, end):
    '''
    Returns a list which contains the namedtuples "box" of all boxes that have been
    found with pdf2textbox.
    The namedtuples contain the x, y - coordinates of every box, and the text.
    First, the boxes are reduced to those in pages between start and end.
    Second, the boxes are reduced to those where the MdL speaks.
    '''
    #print('_speech_converter')
    #for i, box in enumerate(boxes):
    #    print(i, box)
    pages = _find_pages_of_interest(boxes, start, end)
    box_list = _find_boxes_with_speech(pages, mdl, kind, first_names,\
            last_names, start, end)

    if box_list == []:
        print('an empty list was encountered in _speech_converter')
        sys.exit()

    return box_list


def _find_boxes_with_speech(pages, mdl, kind, first_names, last_names, start, end):
    '''
    This function is a bit tricky. Its purpose is to put those boxes that contain
    the MdL's speech into a list, and none others. To this end I need to take a
    close look at those boxes' text, but after that I will still have those boxes
    in their original state (which means that ridding them of remarks and other
    unwanted stuff will have to be done all over again).
    The reason for this is that this will enable me to correct blunders that PDF
    will inevitably commit. It also means that I will have to spend far more time
    converting PDF to text than otherwise :(

    Returns a list that contains all boxes with the actual MdL's speech (still
    containing the remarks and header items etc.)
    '''
    print()
    print('_find_boxes_with_speech starting here')
    box_list = list()
    token_speaks = False
    is_question = False

    for j, page in enumerate(pages):
        print('starting a new page:', j+int(start))
        for k, vv in page.items():          # k: header, columns
            print('starting a new column (or header) here:', k)
            print('key: ', k)
            print('kind:', kind)
            print('is_question:', is_question)
            print('token_speaks:', token_speaks)
            print()
            for i, box in enumerate(vv):    # vv: list with boxes
                #print(f'{i} token_speaks:{token_speaks}')
                #print('.', box)
                box_text = _prepare_text(box.text, start, end, applause=True,\
                        name='_find_boxes_with_speech a')
                #print('..', box_text)
                if _has_no_text(box_text):
                    continue
                if not token_speaks and int(start) == int(end) and j > 1:
                    return box_list
                elif kind == 'speech':
                    if not token_speaks and _is_speaker(box_text, mdl, start, end):
                        box_list.append(box)
                        token_speaks = True
                    elif token_speaks:
                        if _is_president(box_text, start, end):
                            token_speaks = False
                            sent = box_list[-1].text
                            applause = True
                            sent = _prepare_text(sent, start, end, applause,\
                                    name='_find_boxes_with_speech b')
                            if sent:
                                #print(sent)
                                if _ends_with_applause(sent):
                                    return box_list
                                elif  _contains_final_words(sent):
                                    return box_list
                            else:
                                continue
                        elif _is_other_MdL(box_text, mdl, first_names, last_names,\
                                start, end):
                            token_speaks = False
                            continue
                        else:
                            box_list.append(box)
                    else:
                        continue
                elif kind != 'speech':
                    #print('branching into question, box-index:', i)
                    #print(box)
                    if not token_speaks and _is_speaker(box_text, mdl, start, end):
                        box_list.append(box)
                        token_speaks = True
                        if _is_question(box_text, start, end):
                            is_question = True
                    elif token_speaks:
                        if 'Fr' in kind and _is_president(box_text, start, end):
                            if is_question:
                                return box_list
                            token_speaks = False
                        elif 'Fr' in kind and _is_other_MdL(box_text, mdl,\
                                first_names, last_names, start, end):
                            print('found other MdL:')
                            if is_question:
                                return box_list
                            token_speaks = False
                        elif 'Fr' in kind and _is_question(box_text, start, end):
                            box_list.append(box)
                            is_question = True
                        elif _is_president(box_text, start, end):
                            token_speaks = False
                        elif _is_other_MdL(box_text, mdl, first_names, last_names,\
                                start, end):
                            token_speaks = False
                        else:
                            box_list.append(box)
                    else:
                        continue

    return box_list


def _find_pages_of_interest(boxes, start, end):
    page_of_interest = False
    pages = list()
    counter = 0
    print('start, end: ', start, end)
    for page_nr, page in boxes.items():     # pagenr counted from 1
        print(f'internal pagenr: {page_nr}, i.e. {int(start)+counter}')
        counter += 1
        for kk, vv in page.items():         # page: dict with header, left and right col
            for box in vv:
                if _is_page_of_interest(box, start, end, page_of_interest):
                    page_of_interest = True
                    pages.append(page)
    print()
    return pages


def _is_page_of_interest(box, start, end, page_of_interest):
    try:
        lines = box.text.split('\n')
    except AttributeError:
        return False
    lines = list(filter(None, lines))
    for line in lines:
        line = line.strip()
        line = re.sub('[!,*]', '', line)
        if line.isdigit():
            if not page_of_interest:
                if int(start) == int(line):
                    page_of_interest = True
                    return page_of_interest
            elif page_of_interest:
                if int(start) < int(line) <= int(end):
                    return page_of_interest
                elif int(line) == int(end)+1:
                    page_of_interest = False
                    return page_of_interest
    return False


def _text_without_header_items(box_text, start, end):
    '''
    I first split the text using .split(' ') but this would also find the (not
    so rare) case when 'Nordrhein-Westfalen' appeared in a speech.
    So now I split with line breaks.
    Another option might be to check that 'Landtag' and 'Nordrhein-Westfalen'
    appear in succession. I'm not convinced of that though.
    '''
    header_words = ['Landtag', 'Nordrhein-Westfalen', 'Plenarprotokoll']

    #print('_text_without_header_items, before:', box_text)
    if box_text:
        try:
            sents = box_text.split('\n')
        except AttributeError:
            sents = box_text
        sents = list(filter(None, sents))
        sents = [e for e in sents if e != ' ']
        if sents == []:
            return None
        #print('sents', sents)
    else:
        return None

    first_sent_wo_header_items = list()
    for i, word in enumerate(sents):
        if i < 5:
            word_to_check = word.strip()
            word_to_check = re.sub('[!,*\n]', '', word_to_check)
            if word_to_check in header_words:
                sents = sents[1:]
                continue
            elif '/' in word_to_check:
                before = word_to_check.split('/')[0]
                after = word_to_check.split('/')[-1]
                if before.isdigit() and after.isdigit():
                    sents = sents[1:]
                    continue
            elif word_to_check.isdigit():
                if int(start) <= int(word_to_check) <= int(end):
                    sents = sents[1:]
                    continue
            else:
                try:
                    datetime.datetime.strptime(word_to_check, '%d.%m.%Y')
                    sents = sents[1:]
                    continue
                except ValueError:
                    first_sent_wo_header_items.append(word)
        else:
            first_sent_wo_header_items.append(word)

    #print('first_sent_wo_header_items', first_sent_wo_header_items)
    first_sent_wo_header_items = list(filter(None, first_sent_wo_header_items))
    if len(first_sent_wo_header_items) > 0:
        if len(first_sent_wo_header_items) == 1:
            if first_sent_wo_header_items[0] in ['\n', ' ', '/']:
                return None
        #first_sentence = ' '.join(word for word in first_sent_wo_header_items)
        #sents[0] = first_sentence
        text = '\n'.join(sent for sent in sents)
        text = text.strip()
        text = re.sub(' +', ' ', text)
        #print('_text_without_header_items, after:', text)
        return text
    return None


def _is_it_page_of_interest(box, start, end):
    page_of_interest = False
    try:
        pagenr = box.text
        pagenr = re.sub('[!,*\n]', '', pagenr)
        if int(pagenr) == int(start):
            page_of_interest = True
        elif int(pagenr) > int(end):
            page_of_interest = False
    except ValueError:
        pass
    except TypeError:
        pass

    return page_of_interest


def _make_new_box(box, text_in_header):
    New_box = namedtuple('New_box', 'x0 x1 y0 y1 text')
    new_box = New_box(x0=box.x0, x1=box.x1, y0=box.y0, y1=box.y1, text=text_in_header)

    return new_box


def _is_speaker(box_text, mdl, start, end):
    '''
    A speaker will be at the very beginning of a box.
    Because it happens that some header shmutz will get there first, this shmutz
    has to be removed with _text_without_header_items.

    I differentiate between first names being compound of several names
    and familiy names being compound of several names.
    Regarding the first names there is a good chance that only one part
    (the so-called "Rufname") is being used in the protocoll.
    The family name will have all parts of it in the protocoll.

    Returns True or False
    '''
    #print()
    #print('_is_speaker starting here')
    first_name = _low_cap_all(mdl.first_name)
    last_name = _low_cap_all(mdl.last_name)
    found_first_name = False

    #print('first_name, last_name', first_name, last_name)

    if not box_text:
        return False
    else:
        #print('box_text in _is_speaker\n', box_text)
        pass

    if len(first_name.split(' ')) > 1:
        first_names = first_name.split(' ')
        l_fn = len(first_names)
    else:
        first_names = None
        l_fn = 1
    if len(last_name.split(' ')) > 1:
        last_names = last_name.split(' ')
        l_ln = len(last_names)
    else:
        last_names = None
        l_ln = 1

    words = box_text
    first_element = words[0]
    #print('first_element', first_element)
    first_word = re.sub(clutter, '', first_element)
    #print('first_word in _is_speaker', first_word, first_name)

    if first_names:
        counter = 0
        while counter < l_fn:
            if first_word in first_names:
                words = words[1:]
                if words == []:
                    return False
                words = _cut_off_peertitle(words)
                first_element = words[0]
                first_word = re.sub(clutter, '', first_element)
                found_first_name = True
                break
            else:
                return False
    else:
        if first_word == first_name:
            #print('found first name ....................')
            found_first_name = True
            words = words[1:]
            first_element = words[0]
            first_word = re.sub(clutter, '', first_element)
            #print('second word in _is_speaker', first_word, last_name)

    if found_first_name:
        counter = 0
        if last_names:
            while counter < l_fn+l_ln:
                counter += 1
                if first_word in last_names:
                    last_names.remove(first_word)
                words = words[1:]
                first_element = words[0]
                first_word = re.sub(clutter, '', first_element)
            if not last_names:
                return True
            else:
                return False
        else:
            if first_word == last_name:
                print(f'***   found MdL {first_name} {last_name} is_speaker   ***')
                print()
                return True
            else:
                return False
    else:
        return False


def _is_muendl_anfrage(box_text, start, end):
    '''
    Sometimes a "Zwischenfrage" or "Zusatzfrage" will be read by the president.
    The procedure is calling a -Mündliche Anfrage- by MdL -first_name last_name-
    of the parliamentary group -party-:
        Ich rufe auf die
                Mündliche Anfrage 367
        der Frau Abgeordneten Andrea Asch von der Frak-
        tion der Grünen:
    I will look for keywords "Mündliche Anfrage".
    Another function will look if the MdL's name is found in the box.

    Returns True or False
    '''
    anfrage = False

    words = _prepare_text(box_text, start, end, name='_is_muendl_anfrage')
    if not words:
        return False

    if 'Mündliche' and 'Anfrage' in words:
        print('found anfrage')
        print(words)
        anfrage = True

    return anfrage


def _is_anfrage_of_mdl(box_text, mdl, start, end):
    '''
    Sometimes a "Zwischenfrage" or "Zusatzfrage" will be read by the president.
    The procedure is calling a -Mündliche Anfrage- by MdL -first_name last_name-
    of the parliamentary group -party-:

        Ich rufe auf die
                Mündliche Anfrage 367
        der Frau Abgeordneten Andrea Asch von der Frak-
        tion der Grünen:

    This function will look for keywords first_name and last_name.
    Of the first_name I only take the first part if the name consists of several
    names. The last name will have to be found completely.

    Returns True or False
    '''

    first_name = _low_cap_all(mdl.first_name)
    fn = first_name.split(' ')[0]
    last_name = _low_cap_all(mdl.last_name)
    last_names = last_name.split(' ')

    words = _prepare_text(box_text, start, end, name='_is_anfrage_of_mdl')
    print(words)
    if not words:
        return False

    if fn in words:
        print('found first_name')
        for name in last_names:
            if name in words:
                continue
            else:
                return False
        return True

    return False


def _is_other_MdL(box_text, mdl, vN_list, nN_list, start, end):
    '''
    Checks if other speaker interrupts (or marks end of speech).
    Returns True or False
    '''
    #print()
    #print('is_other_MdL starting here')
    first_name = mdl.first_name
    last_name = mdl.last_name
    indexes = list()
    names_to_check = list()

    #words = _prepare_text(box_text, start, end)
    if not box_text:
        return False
    else:
        #print('box_text in _is_other_MdL\n', box_text)
        pass

    words = box_text
    if words == []:
        return false
    words = _cut_off_akad_titel(words)
    first_element = words[0]
    first_word = re.sub(clutter, '', first_element)
    #print('first_word:', first_word)
    first_word_upper = ''.join([c.upper() if c != 'ß' else c for c in first_word])
    while True:
        if first_word_upper in vN_list:
            names_to_check.append(first_word)
            words = words[1:]
            if words is None:
                break
            first_element = words[0]
            first_word = re.sub(clutter, '', first_element)
            first_word_upper = ''.join([c.upper() if c != 'ß' else c for c in first_word])
            #print('first_word (actually next word):', first_word)
        else:
            break

    if names_to_check:
        #print('first_word_upper:', first_word_upper)
        if first_word_upper in nN_list:
            if first_word_upper != last_name:
                return True
        else:
            for name in nN_list:
                if first_word_upper in name:
                    return True
    else:
        return False


def _prepare_text(box_text, start, end, applause=False, name=None):
    '''
    Will look for text that belongs into the header and take it out
        --> clean_box_text
    Will look for remarks having a pattern like this:
        (Name of MdL [party]: some remark)
        Since this can contain line breaks as well as remarks from other MdLs
        I reduced the pattern to this:
            (anything linebreaks anything)
    # Finally the text is scanned for academic titles which will be removed.

    Returns a list of words
    '''
    #print()
    #print('_prepare_text starting here')
    #print('box_text before')
    #print(box_text)
    if box_text:
        try:
            box_text = box_text.strip()
        except AttributeError:
            box_text = '\n'.join(sent for sent in box_text)
            box_text = box_text.strip()
        try:
            if box_text[0] == '(' and box_text[-1] == ')':
                return None
        except IndexError:
            return None
    clean_box_text = _text_without_header_items(box_text, start, end)
    if not clean_box_text:
        return None

    #print('box_text --> clean_box_text')
    #print(clean_box_text)
    if applause:
        words = clean_box_text.split(' ')
        words = list(filter(None, words))
        if '(Beifall' in words:
            words = [w for w in words if w != '\n']
            return words

    clean_box_text = _find_and_replace_remarks(clean_box_text)

    words = clean_box_text.split(' ')
    words = list(filter(None, words))
    words = [w for w in words if w != '\n']
    if words == []:
        return None
    #words = _cut_off_akad_titel(words)

    return words


def _find_and_replace_remarks(clean_box_text):
    #print()
    #print('_find_and_replace_remarks starting here')
    # I cannot loop over these patterns putting them in a list because list will
    # not follow my intention of taking remark_pattern1 first.
    remark_pattern1 = re.compile('^\(.*\n*.*\)$')
    remark_pattern2 = re.compile('\((Beifall|Zuruf) .*\)')
    remark_pattern3 = re.compile('\[.*\]\:.*')

    lines = clean_box_text.split('\n')
    clean_box_text = list()
    for i, line in enumerate(lines):
        #print(i, line, len(line))
        m1 = re.search(remark_pattern1, line)
        m2 = re.search(remark_pattern2, line)
        m3 = re.search(remark_pattern3, line)
        if m1:
            line = _replace_remark_patterns(m1, line)
        elif m2:
            line = _replace_remark_patterns(m2, line)
        elif m3:
            line = _replace_remark_patterns(m3, line)
        clean_box_text.append(line)
    clean_box_text = '\n'.join(line for line in clean_box_text if line)

    return clean_box_text


def _replace_remark_patterns(m, line):
    parties = ['(GRÜNE)', '(SPD)', '(CDU)', '(FDP)', '(PIRATEN)', '(AfD)']
    pattern = m[0]
    #print('pattern', pattern)
    if pattern in parties:
        pass
    else:
        new_line = line.replace(pattern, '')
        #print('line without remark:')
        #print(new_line)

    return new_line


def _cut_off_akad_titel(words):
    acad_titles = ['Dr.', 'Prof.', 'Dr.Dr.', 'Prof.Dr.']
    try:
        first_word = words[0]
    except IndexError:
        print(words)
        raise
    while first_word in acad_titles:
        words = words[1:]
        first_word = words[0]
    return words


def _cut_off_peertitle(words):
    peer_titles = ['von', 'van', 'zur', 'auf', 'der', 'de', 'Freifrau', 'Freiherr',\
            'Gräfin', 'Graf', 'vom']
    try:
        first_word = words[0]
    except IndexError:
        print(words)
        raise
    while first_word in peer_titles:
        if len(words) > 1:
            words = words[1:]
            first_word = words[0]
    return words


def _collect_speech_in_list(box_dict):
    speech_list = list()
    for k, v in box_dict.items():
        for kk, vv in v.items():
            if len(vv) > 1:
                raise('wf15, _collect_speech_in_list')
            speech_list.append(vv[0].text)

    return speech_list


def _get_rid_of_remarks(box_list_to_iterate):
    '''
    This function will get rid of all remarks like
        (Beifall von ...)
    which will be part of the protocol but not part of the speech.
    To remove a remark like this it needs to be in its own box.
    Sometimes remarks will be only seperated by a line break. These need
    to be take care of in a seperate function.
    '''
    #print()
    #print('_get_rid_of_remarks starting here')
    box_list = list()
    for i, box in enumerate(box_list_to_iterate):
        box_text = box[0]
        print(i, box_text)
        if _has_no_text(box_text):
            continue
        box_text = box_text.strip()
        if _is_remark(box_text):
            print('box_text being a remark and neglected', box_text)
            continue
        else:
            box_list.append([box_text])

    return box_list


def _has_no_text(box_text):
    if box_text == None:
        return True
    else:
        try:
            box_text = box_text.strip()
            if box_text[0]:
                return False
        except IndexError:
            return True
        except AttributeError:
            if box_text[0]:
                return False


def _is_remark(box_text):
    '''
    Checks if a box contains a remark (will be in bracklets).
    Returns True or False.
    '''

    try:
        box_text = box_text.strip()
        if box_text[0] == '(' and box_text[-1] == ')':
            for line in box_text.split('\n'):
                line = line.strip()
                if line[0] == '(' and line[-1] == ')':
                    pass
                else:
                    return False
            print('_is_remark\n', box_text)
            return True
        else:
            return False
    except IndexError as e:
        #raise           # because box_text without text should be taken care of
        return True


def _get_rid_of_remarks_sep_by_linebreak(box_text):
    '''
    This function will get rid of all remarks like
        (Beifall von ...) \n
    which will be part of the protocol but not part of the speech.
    To remove a remark like this the text needs to be seperated by
    linebreaks. Then those parts will be tried for brackets and taken
    out. The rest of the text will be joined again.
    Since this only works once I have left the box structure (the
    namedtuples cannot be changed) this function can only be called
    once I only work with text.
    '''
    new_text = ''
    box_text = box_text.strip()
    sentences = box_text.split('\n')
    for sentence in sentences:
        try:
            if sentence[0] == '(' and sentence[-1] == ')':
                print('skipping sentence: ', sentence)
                continue
            else:
                new_text = new_text + sentence + ' '
        except IndexError:
            pass
    box_text = new_text

    return box_text


def _is_president(box_text, start, end):
    '''
    The president will remind the speaker that time is over or thank the speaker
    and introduce the next one. It should not be part of anyone's speech.
    Returns True or False
    '''

    #words = _prepare_text(box_text, start, end)
    words = box_text
    if not words:
        return False

    first_element = words[0]
    first_word = re.sub(clutter, '', first_element)
    # "räsident" takes care of Präsident, Präsidentin, Vizepräsident/in
    if 'räsident' in first_word:
        print('Found president')
        #print(words)
        return True
    else:
        return False


def _is_question(box_text, start, end):
    '''
    If kind of contribution is a 'Zwischenfrage' or 'Zusatzfrage', it usually ends
    with a questionmark. To prevent that several contributions will be lumped for
    one I decided to test this condition.
    Returns True or False
    '''

    #print('_is_question starting here')
    #print(box_text)
    words = box_text
    if not words:
        return False

    last_element = words[-1].strip()
    if last_element[-1] == '?':
        print('Found question')
        #print(words)
        return True
    else:
        return False


def _get_rid_of_line_breaks_wth_hyphens(sents, mdl_names):
    #print()
    #print('_get_rid_of_line_breaks_with_hyphens')
    puncts = ['.', '!', '?']
    new_sentences = list()
    for j, sent in enumerate(sents):
        #print(j, sent)
        skip = False
        while '-\n' in sent:
            new_sentence = ''
            parts = sent.split('-\n')
            for i, part in enumerate(parts):
                if skip:
                    skip = False
                    continue
                words = part.split(' ')
                words = list(filter(None, words))
                if not words:
                    new_sentence += '-'
                    #skip = True
                    continue
                else:
                    last_word = words[-1].strip()

                try:
                    next_part = parts[i+1]
                except IndexError:
                    part = part.strip()
                    new_sentence += part
                    continue

                if not next_part:
                    continue
                next_words = next_part.split(' ')
                next_words = list(filter(None, next_words))
                first_word = next_words[0].strip()
                save_for_later = list()
                while True:
                    if first_word[-1].isalnum():
                        break
                    else:
                        save_for_later.insert(0, first_word[-1])
                        first_word = first_word[:-1]
                save_for_later = ''.join(c for c in save_for_later)
                new_word = last_word + first_word
                new_word = _find_correct_spelling(new_word, mdl_names,\
                    last_word, first_word, name='get_rid_of_line_breaks_with_hyphens')
                if not new_word:      # should not occur! because of "if not words"
                    print('words:', words)
                    print('next_words:', next_words)
                    print('new_word:', new_word)
                    raise Exception('_get_rid_of_line_breaks_with_hyphen')
                if save_for_later:
                   new_word += save_for_later
                combined_parts = words[:-1] + [new_word] + next_words[1:]
                combined_parts = ' '.join(word for word in combined_parts)
                part = combined_parts.strip()
                if part[-1] in puncts:
                    part += '\n'
                else:
                    part += '-\n'
                new_sentence += part
                skip = True
                #print(new_sentence)
            sent = new_sentence
        new_sentences.append(sent)

    return new_sentences


def _get_rid_of_line_breaks(sents):
    sentences = list()

    for sentence in sents:
        sentence = re.sub('\n', '', sentence)
        if sentence.startswith(' '):
            sentence = sentence[1:]
        sentences.append(sentence)

    return sentences


def _find_words_sep_by_hyphens(sents, mdl_names):
    skip = False
    sentences = list()

    #print('i, sentence in _find_words_sep_by_hyphens in:')
    for i, sentence in enumerate(sents):
        #print(i, sentence)
        if skip:
            skip = False
            continue
        new_sentence = ''
        words = sentence.split(' ')
        words = list(filter(None, words))
        new_words = list()      # words to make a correct sentence
        last_word = words[-1]
        last_word = last_word.strip()
        if last_word[-1] == '-':
            try:
                next_sentence = sents[i+1]
            except IndexError:
                new_sentence = sentence
                continue
                #raise Exception('Sentence ends with hyphen but there is no second part to that word!')
            next_words = next_sentence.split(' ')
            next_words = list(filter(None, next_words))
            first_word = next_words[0]
            without_hyphen = last_word[:-1] + first_word
            print('without_hyphen', without_hyphen)
            new_word = re.sub(clutter, '', without_hyphen)
            new_word = _find_correct_spelling(new_word, mdl_names, last_word,\
                    first_word, name='_find_words_sep_by_hyphens')
            new_sentence += ' '.join(w for w in words[:-1] + [new_word] + next_words[1:])
            skip = True
        else:
            new_sentence = sentence

        sentences.append(new_sentence)

    #print('i, sent after find_words_sep_by_hyphens: ~~~~~~~~~~~~~~')
    #for i, sent in enumerate(sentences):
    #    print(i, sent)

    return sentences


def _find_words_sep_by_hyphens_within_sentence(sents, mdl_names):
    sentences = list()
    take_punctuation_mark = False

    for i, sentence in enumerate(sents):
        words = sentence.split(' ')
        words = list(filter(None, words))
        #print('words, checking for hyphens', words)
        new_words = list()      # words to make a correct sentence
        skip = False
        for j, word in enumerate(words):
            if skip:
                skip = False
                continue
            elif word[-1] == '-':
                try:
                    next_word = words[j+1]
                except IndexError:
                    new_words += [word]
                    continue
                    #raise Exception('Sentence ends with hyphen but there is no second part to that word!')
                without_hyphen = word[:-1] + next_word
                if without_hyphen[-1].isalpha():
                    new_word = without_hyphen
                else:
                    new_word = without_hyphen[:-1]
                    take_punctuation_mark = True
                new_word = _find_correct_spelling(new_word, mdl_names, word,\
                        next_word, name='_find_words_sep_by_hyphens')
                #print('new_word (aka without_hyphen)', new_word)
                if take_punctuation_mark:
                    take_punctuation_mark = False
                    new_word = without_hyphen
                new_words += [new_word]
                skip = True
                #print('new_words', new_words)
            else:
                new_words += [word]
        new_sentence = ' '.join(w for w in new_words)
        #print('final sentence after getting rid of hyphens\n', new_sentence)
        sentences.append(new_sentence)

    return sentences


def _find_last_remarks(sents):
    skip = False
    sentences = list()
    remark_pattern = re.compile('\[.*\]\:.*')

    for i, sent in enumerate(sents):
        m = re.search(remark_pattern, sent)
        if skip:
            skip = False
            continue
        elif sent.startswith('(') and sent.endswith(')'):
            continue
        elif sent.startswith('(Beifall') or sent.startswith('(Zuruf'):
            print(sent)
            try:
                next_sent = sents[i+1]
                if next_sent[-1] == ')':
                    skip = True
                    print(f'****** skipped ******\n{sent}\n{next_sent}')
                    print()
            except IndexError:
                sentences.append(sent)
                continue
        elif m:
           continue
        else:
            sentences.append(sent)

    return sentences


def _contains_final_words(sent):
    '''
    Check if a sentence ends or contains words that indicate the end of the speech.
    'Danke' will not be considered as they are too weak as an
    indication.
    '''
    #print('sent in _contains_final_words\n', sent)
    try:
        words = sent.split(' ')
    except AttributeError:
        words = sent

    if 'danke' in words and 'Ihnen' in words and 'Aufmerksamkeit.' in words:
        #print(words)
        return True
    elif 'Dank' in words and 'Aufmerksamkeit.' in words:
        #print(words)
        return True
    elif 'Vielen' in words and 'Dank.' in words:
        #print(words)
        return True
    elif 'danke' in words and 'Ihnen.' in words:
        #print(words)
        return True
    elif 'Schönen' in words and 'Dank.' in words:
        #print(words)
        return True
    elif 'Herzlichen' in words and 'Dank.' in words:
        #print(words)
        return True
    else:
        return False


def _ends_with_applause(sent):
    try:
        words = sent.split(' ')
    except AttributeError:
        words = sent

    if '(Beifall' in words:
        #print('sent in _ends_with_applause\n', sent)
        #print('*'*70)
        #print('exit with True')
        return True
    #print('exit with False')
    return False


def _correct_PDF_blunder(sent, next_sent):
    isolated_part = sent
    words = sent.split(' ')

    skip, corrected_text = _move_isolated_part_within_text(isolated_part, words)

    if not skip:
        isolated_part = sent
        lines = next_sent.split(' ')
        skip, corrected_text = _move_isolated_part_within_text(isolated_part, lines)

    return skip, corrected_text


def _move_isolated_part_within_text(isolated_part, words):
    skip = False
    corrected_text = None
    words = list(filter(None, words))
    words_to_iterate = words[:]
    l = len(words)
    print('isolated_part', isolated_part)
    for i in range(l+1):
        words_to_iterate.insert(i, isolated_part)
        print(words_to_iterate)
        check = input('Does this match? y/.')
        if check == 'y':
            corrected_text = ' '.join(w for w in words_to_iterate)
            skip = True
            break
        else:
            words_to_iterate = words[:]

    return skip, corrected_text


def _find_correct_spelling(new_word, mdl_names, last_word, first_word, name):
    global german_words
    global german_stopwords
    global hyphened_words
    #print()
    #print('_find_correct_spelling starting here')
    #print('name of calling function:\t', name)
    # check if hyphen
    if last_word[-1] == '-':
        pass
    else:
        last_word += '-'
    with_hyphen = last_word + first_word
    without_hyphen = last_word[:-1] + first_word
    # first without hyphen
    if _is_url_or_mail_address(new_word):
        return new_word
    elif new_word in german_stopwords:
        return new_word
    elif new_word in german_words:
        return new_word
    # now with hyphen
    else:
        new_word_w_clutter = last_word + first_word
        new_word = re.sub(clutter, '', new_word_w_clutter)
        with_hyphen = re.sub(clutter, '', last_word + first_word)
        without_hyphen = re.sub(clutter, '', last_word[:-1] + first_word)
        with_space = last_word + ' ' + first_word
        without_space = last_word[:-1] + first_word
        with_2_spaces = last_word[:-1] + ' - ' + first_word
        with_space_n_hyphen = last_word[:-1] + ' -' + first_word
        if new_word in hyphened_words:
            return new_word
        elif new_word_w_clutter in hyphened_words:
            return new_word_w_clutter
        elif new_word in mdl_names:
            return new_word
        elif with_hyphen in hyphened_words:
            return with_hyphen
        elif without_hyphen in hyphened_words:
            return without_hyphen
        elif with_hyphen in mdl_names:
            return with_hyphen
        elif without_hyphen in mdl_names:
            return without_hyphen
        elif with_hyphen in german_words:
            return with_hyphen
        elif without_hyphen in german_words:
            return without_hyphen
        elif with_space in german_words:
            return with_space
        elif with_space in hyphened_words:
            return with_space
        elif with_space in hyphened_combis:
            return with_space
        elif with_space_n_hyphen in hyphened_combis:
            return with_space_n_hyphen
        elif with_2_spaces in german_words:
            return with_2_spaces
        elif with_2_spaces in hyphened_words:
            return with_2_spaces
        # found neither with nor without hyphen
        else:
            #with_space = last_word + ' ' + first_word
            #with_2_spaces = last_word[:-1] + ' - ' + first_word
            print('_find_correct_spelling')
            print(f'1: {without_hyphen} --> will be saved in standard dict')
            print(f'2: {with_hyphen} --> will be saved in words with hyphen')
            print(f'3: {without_hyphen} --> will be saved in words with hyphen')
            print(f'4: {new_word_w_clutter} --> will be saved in words with hyphen')
            print(f'5: {with_space} --> will be saved in hyphened combos')
            print(f'6: {with_space_n_hyphen} --> will be saved in hyphened combos')
            print(f'7: {with_2_spaces}')
            print(f'8: {without_space}')
            choose = input('1, 2, 3, 4, 5, 6 or . if correction: ')
            if choose == '1':
                _save_standard_dict(without_hyphen)
                return without_hyphen
            elif choose == '2':
                _save_hyphened_expression(with_hyphen)
                return with_hyphen
            elif choose == '3':
                _save_hyphened_expression(without_hyphen)
                return without_hyphen
            elif choose == '4':
                _save_hyphened_expression(new_word_w_clutter)
                return new_word_w_clutter
            elif choose == '5':
                _save_hyphened_combo(with_space)
                return with_space
            elif choose == '6':
                _save_hyphened_combo(with_space_n_hyphen)
                return with_space_n_hyphen
            elif choose == '7':
                return with_2_spaces
            elif choose == '8':
                return without_space
            else:
                corrected_word = input('Corrected word: ')
                print()
                with open('./parli_data/new_german_words.txt', 'a',\
                        encoding='utf-8') as fout:
                    fout.write('\n')
                    fout.write(corrected_word)
                print(f'Added to dict: "{corrected_word}"')
                ok = input('Also add to speech? ./n')
                if ok == 'n':
                    speech_word = input('Speech word: ')
                    return speech_word
                else:
                    return corrected_word


def _save_hyphened_expression(new_word_with_hyphen):
    with open('./parli_data/new_hyphened_words.txt', 'a',\
            encoding='utf-8') as fout:
        fout.write('\n')
        fout.write(new_word_with_hyphen)


def _save_standard_dict(word):
    with open('./parli_data/new_german_words.txt', 'a',\
            encoding='utf-8') as fout:
        fout.write('\n')
        fout.write(word)


def _save_hyphened_combo(combi):
    with open('./parli_data/new_hyphened_combis.txt', 'a',\
            encoding='utf-8') as fout:
        fout.write('\n')
        fout.write(combi)


def _get_rid_of_remarks_within_box(boxes):
    #print()
    #print('_get_rid_of_remarks_within_box')
    box_list = list()
    for j, box in enumerate(boxes):
        for text in box:
            if _is_remark_leftover(text):
                #print(text)
                continue
            new_text = ''
            lines = text.split('\n')
            l = len(lines)
            for i in range(l):
                line = lines[i]
                line = line.strip()
                #print('line:', line)
                if line.startswith('(Beifall') or line.startswith('(Zuruf'):
                    continue
                elif line.startswith('(') and line.endswith(')'):
                    continue
                if i+1 < l:
                    new_text += ' ' + line + '\n'
                else:
                    new_text += ' ' + line
            box_list.append([new_text])

    #for i, box in enumerate(box_list):
    #    print(i, box)
    #sys.exit()
    return box_list


def _is_remark_leftover(box):
    first_word = box[0].split(' ')[0]
    if first_word[0] == '[':
        if first_word[-1] == ':' and first_word[-2] == ']':
            return True
    return False


def _connect_boxes(box_list, german_words, mdl_names):
    '''
    Connects all boxes to one single text block.
    I consider only two cases:
        - There is a hyphen at the end of the last word of a box
            --> will that be one word with first word of next box?
        - Otherwise just connect boxes with a space in between.

    Returns a string
    '''

    skip = False
    complete_text = ''

    for i, box in enumerate(box_list):
        #print('connecting boxes:', i)
        #print(box)
        if skip:
            skip = False
            continue
        if box == []:
            continue
        box_text = box[0].strip(); #print(i, box_text)
        if not box_text:
            continue
        try:
            next_box = box_list[i+1];
        except IndexError:
            complete_text += ' ' + box_text
            continue
        if next_box == []:
            complete_text += ' ' + box_text
            continue
        words = box_text.split(' ')
        words = list(filter(None, words))
        next_box_text = next_box[0].strip()
        #nbt = next_box_text.split('\n')[0]
        #print('\tfirst part of next_box:', nbt)
        next_words = next_box_text.split(' ')
        next_words = list(filter(None, next_words))
        if box_text[-1] == '-':
            save_for_later = list()
            last_word = words[-1].strip()[:-1]
            if not last_word:
                complete_text += ' ' + box_text
            else:
                first_word = next_words[0].strip()
                while True:
                    if first_word[-1].isalnum():
                        break
                    else:
                        save_for_later.insert(0, first_word[-1])
                        first_word = first_word[:-1]
                save_for_later = ''.join(c for c in save_for_later)
                new_word = last_word + first_word
                new_word = _find_correct_spelling(new_word, mdl_names,\
                        last_word, first_word, name='_connect_boxes')
                if save_for_later:
                    new_word += save_for_later
                combined_boxes = words[:-1] + [new_word] + next_words[1:]
                combined_box_text = ' '.join(w for w in combined_boxes)
                complete_text += ' ' + combined_box_text
                skip = True
        else:
            complete_text += ' ' + box_text

    #print()
    #print(complete_text)
    #sys.exit()
    return complete_text


def _old_box_connector(box_list_to_iterate, german_words, mdl_names):
    box_list = list()
    complete_text = ''
    skip = False
    prefixes = ['ab', 'äg', 'al', 'am', 'an', 'än', 'ar', 'as', 'aß',\
                                                        'at', 'ät', 'au',\
            'be', 'ch',\
            'da', 'de', 'di', 'dü',\
            'ei', 'eg', 'el', 'en', 'er', 'es', 'eß',\
            'fa', 'fe', 'ge', 'gs',\
            'ha', 'hä', 'he', 'hm', 'hn', 'ht',\
            'ic', 'ie', 'if', 'il', 'im', 'in', 'ir', 'is', 'it',\
            'ka', 'ke', 'ks', 'ku',\
            'la', 'le', 'li', 'lo', 'mi', 'mm', 'mö',\
            'nd', 'ne', 'ng', 'nn', 'ns', 'nt',\
            'ob', 'om', 'on', 'ön', 'op', 'or', 'ör', 'os', 'oß',\
            'pa', 'pä', 'pe', 'pi', 'po',\
            're', 'rm', 'rn', 'ro', 'rö',\
            'sc', 'se', 'si', 'ss', 'st',\
            'te', 'ti', 'to', 'tz',\
            'uf', 'üf', 'um', 'un', 'ün', 'us', 'uß', 'ür', 'üs',\
            'wi', 'wü', 'zu']
    Prefixes = [syll.capitalize() for syll in prefixes]

    for i, box in enumerate(box_list_to_iterate):
        #print(i, box)
        next_box_text = None
        if box != []:
            box_text = box[0].strip()
            box_words = box_text.split(' ')
            box_words = list(filter(None, box_words))
        elif box == []:
            continue
        else:
            break
        try:
            if box_list_to_iterate[i+1]:
                next_box_text = box_list_to_iterate[i+1][0]
                next_box_text = next_box_text.strip()
                next_box_words = next_box_text.split(' ')
                next_box_words = list(filter(None, next_box_words))
            elif box_list_to_iterate[i+1] == []:
                complete_text += ' ' + box_text
                skip = True
        except IndexError:
            if not skip:
                complete_text += ' ' + box_text
            break

        if skip:
            skip = False
            continue
        elif box_text and box_text[-1] == '-':
            if box_text[-2] == ' ':
                complete_text += ' ' + box_text + ' ' + next_box_text
                skip = True
                break
            elif next_box_text and box_text[-3:-1] in prefixes:
                complete_text += ' ' + box_text[:-1] + next_box_text
                skip = True
            elif next_box_text and box_text[-3:-1] in Prefixes:
                complete_text += ' ' + box_text[:-1] + next_box_text
                skip = True
            elif next_box_text and next_box_words[0] in ['und', 'oder']:
                complete_text += ' ' + box_text + ' ' + next_box_text
                skip = True
            elif next_box_text and next_box_text[0].islower():
                new_word = box_words[-1][:-1] + next_box_words[0]
                if new_word in german_words:
                    complete_text += ' ' + box_text[:-1] + next_box_text
                    skip = True
            elif next_box_text and next_box_text[0].isupper():
                complete_text += ' ' + box_text + next_box_text
                skip = True
            else:
                complete_text = complete_text + ' ' + box_text
        elif box_text and box_text[-1] == ',':
            if next_box_text:
                complete_text += ' ' + box_text + ' ' + next_box_text
                skip = True
        elif box_text and box_text[-1] == ':':
            if next_box_text:
                complete_text += ' ' + box_text + ' ' + next_box_text
                skip = True
        else:
            complete_text += ' ' + box_text

    complete_text = re.sub(' +', ' ', complete_text)
    #complete_text = re.sub('([a-zäöüß])- ([a-zäöü])', r'\1\2', complete_text)

    print('+++ complete_text +++', complete_text)
    return complete_text


def _is_word_in_vN_list(word, first_name, vN_list):
    if word in vN_list and word != first_name:
        return True
    else:
        return False


def _get_rid_of_name(boxes, mdl, start, end):
    '''
    Take out the speaker's name from the start of the speech, occasionally from
    somewhere within.
    Pattern is always: "First name, last name (party):"
    Seperate by colon, check out if name at the beginning of sentence. This can
    still be assumed to be the case since I have not yet connected the speech
    boxes to one speech.
    Returns the list of boxes without the speaker's name.
    '''
    #print()
    #print('_get_rid_of_name is starting here')
    box_list = list()
    first_name = mdl.first_name.split(' ')
    last_name = mdl.last_name.split(' ')
    full_name = first_name + last_name
    name_count = len(first_name) + len(last_name)
    print(full_name, name_count)

    #print('+'*40)
    for i, box in enumerate(boxes):
        #print(i, box)
        _is_name = False
        box_text = box[0].strip()
        box_text = re.sub(' +', ' ', box_text)
        beginning = box_text.split('):')[0]
        #print("box_text.split('):')", box_text.split('):'))
        beginning = beginning.split(' ')[:-1]
        #print('beginning.split(' ')[:-1]', beginning)
        _is_name = _is_speaker(beginning, mdl, start, end)
        if _is_name:
            #print('box_text', box_text)
            box_text = box_text.split('):')[1:]
            #print('box_text.split("):")[1:]', box_text)
            box_list.append(box_text)   # this is a list already!!
        else:
            box_list.append([box_text])

    #print('box_list after getting rid of name')
    #for i, box in enumerate(box_list):
    #    print(i, box)

    return box_list


def _sentence_starts_with_name(sentence, name):
    words_in_sentence = sentence.split(' ')
    token = False
    if len(name.split(' ')) > 1:
        names_in_name = name.split(' ')
        for word in names_in_name:
            if words_in_sentence[0] == word:
                words_in_sentence = words_in_sentence[1:]
                token = True
            elif token:
                return True
            else:
                return False
        return True
    else:
        if words_in_sentence[0] == name:
            return True


def _shorten_sentence(sentence, name):
    _by = len(name) + 1
    shortened_sentence = sentence[_by:]

    return shortened_sentence


def _get_rid_of_greeting(sentences):
    '''
    The final speech has no need of containing the MdL's greetings at the beginning.

    Returns the speech without the speaker addressing the president and his
    colleagues.
    '''
    final_speech = list()
    for i, sentence in enumerate(sentences):
        if sentence.endswith('Herren!'):
            continue
        elif sentence.endswith('Kollegen!'):
            continue
        elif sentence.endswith('Präsident!'):
            continue
        elif sentence.endswith('Präsidentin!'):
            continue
        elif sentence.startswith('Sehr'):
            if 'geehrte' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            elif 'verehrte' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
        elif sentence.startswith('Liebe'):
            if 'Kolleg' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            elif 'Gäste' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            else:
                final_speech.append(sentence)
        elif sentence.startswith('Meine'):
            if 'Kolleg' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            elif 'sehr' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            elif 'Damen' in sentence.split(' ')[1]:
                if sentence[-1] == '!':
                    continue
                else:
                    final_speech.append(sentence)
            else:
                final_speech.append(sentence)
        else:
            final_speech.append(sentence)

    return final_speech


def _consider_quotes(sentences):
    '''
    Will recognize beginning of quotes if they start with \u201E and will collect
    quotes in a seperate list until end of quote marked by \u201C is reached.
    (German text, German quotation).
    The quote will then be inserted into the MdL's speech as if it was ONE single
    sentence.
    New problem: sometimes it's not quoting a third party but an idiom or saying.
    To not have every idiom come up in a seperate line the selection is added by
    looking for ':' before \u201E.
    '''
    sents_w_quotes = list()
    quotation = list()
    quoting = False
    end_of_quote = False
    for nr_of_sent, sent in enumerate(sentences):
        #print(nr_of_sent, sent)
        sent_range = len(sent)
        sent_after_quote = ''
        sent_before_quote = ''
        for index in range(sent_range):
            c = sent[index]
            if not quoting and c == '\u201E':
                if ':' in sent[index-3:index]:
                    # "After the quote is before the quote." (Sepp Herberger)
                    if sent_after_quote != '':
                        sents_w_quotes.append(sent_after_quote.lstrip())
                        sent_after_quote = ''
                    elif index > 0:
                        sent_before_quote = sent[:index]
                        sents_w_quotes.append(sent_before_quote.lstrip())
                        sent_before_quote = ''
                    quote = c
                    quoting = True
                    end_of_quote = False
            elif quoting and c == '\u201C':
                quote += c + ' '
                quotation.append(quote.lstrip())
                sents_w_quotes += quotation
                quotation = list()
                quoting = False
                end_of_quote = True
                quote = ''
            elif quoting and c != '\u201C':
                quote += c
            elif end_of_quote:
                sent_after_quote += c
        try:
            quote += ' '
            if sent_after_quote.lstrip()[0] in ['.', '!', '?', ',']:
                pass
            elif sent_after_quote != '':
                sent_after_quote += ' '
                sents_w_quotes.append(sent_after_quote.lstrip())
                sent_after_quote = ''
        except (UnboundLocalError, IndexError):
            pass
        if end_of_quote:
            end_of_quote = False
            try:
                first_char = sent_after_quote.strip()[0]
                if first_char in ['.', '!', '?']:
                    sents_w_quotes[-1] = sents_w_quotes[-1].rstrip() + first_char
                elif first_char == ',':
                    sents_w_quotes[-1] = sents_w_quotes[-1] + sent_after_quote
                elif sent_after_quote != '':
                    sents_w_quotes.append(sent_after_quote.lstrip())
                    sent_after_quote = ''
            except IndexError:
                pass
        elif not quoting:
            sents_w_quotes.append(sent.lstrip())

    return sents_w_quotes


def _open_dilled_wp(legislature):
    '''
    '''
    try:
        dir_ = f'/home/frodo/Python-Projekte/parli_NRW/parli_NRW/data/WP{legislature}/'
        print(os.listdir(dir_))
        latest_file = dir_ + sorted(os.listdir(dir_))[-1]
        print(f'opening: {latest_file}')
        with open(latest_file, 'rb') as fin:
            wp = dill.load(fin)
    except (FileNotFoundError, IsADirectoryError):
        try:
            print(f'did not find {latest_file}')
            dir_local = f'./parli_data/wf15_dilled_wps/'
            file_local = dir_local + 'WP_{}.dill'.format(legislature)
            print(f'opening file: {file_local}')
            with open(file_local, 'rb') as fin:
                wp = dill.load(fin)
        except FileNotFoundError:
            dir_loc = f'./parli_data/wf13_contributions/'
            file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
            print(f'opening file: {file_loc}')
            with open(file_loc, 'rb') as fin:
                wp = dill.load(fin)
    except IndexError:
        try:
            print(f'did not find a file in {dir_}')
            dir_local = f'./parli_data/wf15_dilled_wps/'
            file_local = dir_local + 'WP_{}.dill'.format(legislature)
            print(f'opening file: {file_local}')
            with open(file_local, 'rb') as fin:
                wp = dill.load(fin)
        except FileNotFoundError:
            dir_loc = f'./parli_data/wf13_contributions/'
            file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
            print(f'opening file: {file_loc}')
            with open(file_loc, 'rb') as fin:
                wp = dill.load(fin)


    return wp


if __name__ == '__main__':
    wf15_convert_PDF2text_and_save()
