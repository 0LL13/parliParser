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
from parli_data.mk_set_of_hyphened_words import mk_list_of_hyphened_words
from parli_data.mk_set_of_german_words import mk_list_of_german_words
from parli_data.mk_set_of_german_stopwords import mk_list_of_stopwords
from parli_data.mk_set_of_mdl_family_names import mk_set_of_mdl_family_names
from parli_data.mk_update_of_german_words import mk_update_of_german_words
from parli_data.mk_update_of_hyphened_words import mk_update_of_hyphened_words
from scraper_lib.ask_for_wahlperiode import ask_for_wahlperiode
from scraper_lib.standardize_name import _low_cap_all


# see https://gist.github.com/zerolab/1633661 for smart double quotes
clutter = '[*!?,.;:_\s()\u201C\u201D\u201E\u201F\u2033\u2036\u0022]'

german_words = mk_list_of_german_words()
german_stopwords = mk_list_of_stopwords()
hyphened_words = mk_list_of_hyphened_words()


def wf15_convert_PDF2text_and_save():
    save = verbose = preview = legislature = False
    try:
        if sys.argv[1] == 's':
            save = True
        elif sys.argv[1] == 'v':
            verbose = True
        elif sys.argv[1] == 'p':
            preview = True

        if sys.argv[2] in ['14', '15', '16']:
            legislature = sys.argv[2]
    except IndexError:
        verbose = True

    if not legislature:
        legislature = ask_for_wahlperiode()

    mk_update_of_german_words()
    mk_update_of_hyphened_words()

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
                    print('final text .............')
                    for i, sent in enumerate(sentences):
                        print(i, sent)

                    #if '16903' in start_end: sys.exit()
                    if '8345' in start_end: sys.exit()
                    token = _save_the_contributions(legislature, key, protocol_nr,\
                            start_end, sentences)

            if token:
                check = input('Continue? ./n')
                if check == 'n':
                    sys.exit()


def _show_actual_contribution(mdl, legislature):
    for protocol_nr, contribution in mdl.contributions.items():
        for start_end, contri in contribution.items():
            if '11167' in start_end:
                print('protocol_nr', protocol_nr)
                print()
                kind = _get_kind_of_contribution(contri)
                start = start_end[0]
                end = start_end[-1]
                for k, sentences in contri.items():
                    if k != 'url':
                        if sentences != 'actual contribution':
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
                    #print('--- dict_of_boxes ---')
                    #for k, v in dict_of_boxes.items():
                    #    print(k, v)
                    boxes = _speech_converter(dict_of_boxes, mdl, first_names,\
                            last_names, kind, start, end)
                    print('--- boxes ---')
                    for i, box in enumerate(boxes):
                        print(i, box)
                    if boxes == []:
                        continue
                    box_list = _mk_list_of_boxes(boxes, start, end)
                    #print('--- box_list ---')
                    #for i, box in enumerate(box_list):
                    #    print(i, box)
                    sentences = _mk_plain_text(box_list, mdl, mdl_names, start, end)
                    yield protocol_nr, start_end, sentences

                elif k != 'url' and v != 'actual contribution':
                    print('.', end='')
                    yield None, None, None


def _mk_plain_text(boxes, mdl, mdl_names, start, end):
    #boxes = _get_rid_of_remarks(box_list)
    #print('--- boxes ---')
    #for i, box in enumerate(boxes):
    #    print(i, box)
    boxes = _get_rid_of_remarks_within_box(boxes)
    boxes = _get_rid_of_name(boxes, mdl, start, end)
    #print('+++ boxes +++')
    #for i, box in enumerate(boxes):
    #    print(i, box)
    complete_text = _connect_boxes(boxes, german_words, mdl_names)
    sentences = nltk.sent_tokenize(complete_text, language='german')
    #print('~~~ sentences after tokenizer ~~~')
    #for i, sent in enumerate(sentences):
    #    print(i, sent)
    sentences = _connect_sentences(sentences)
    sentences =  _get_rid_of_line_breaks_wth_hyphens(sentences, mdl_names)
    sentences = _get_rid_of_line_breaks(sentences)
    sentences = _find_words_sep_by_hyphens(sentences, mdl_names)
    sentences =  _find_words_sep_by_hyphens_within_sentence(sentences, mdl_names)
    sentences = _find_last_remarks(sentences)
    sentences = _find_final_phrase(sentences)
    print('### sentences ###')
    for i, sent in enumerate(sents_w_quotes):
        print(i, sent)
    sys.exit()

    return sentences


def _mk_list_of_boxes(boxes, start, end):
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
    box_list = list()
    sep_boxes_before = list()
    sep_boxes_after = list()
    words = new_text = ''
    nr_of_sep_boxes_before = 0       # tells how many boxes to take out of box_list
    nr_of_sep_boxes_after = 0        # tells how many boxes to skip later on
    for i, box in enumerate(boxes):
        #print(i, box)
        if nr_of_sep_boxes_after > 0:
            print('nr_of_sep_boxes_after > 0, snipping this box:')
            print(i, box)
            nr_of_sep_boxes_after -= 1
            continue
        elif _could_be_box_w_missing_text(box):
            box_coords = _get_coords(box)
            sep_boxes_before = _find_sep_boxes(i, boxes, box_coords, before=True)
            sep_boxes_after = _find_sep_boxes(i, boxes, box_coords, after=True)
            if len(sep_boxes_before) > 0:
                new_text, nr_of_sep_boxes_before =\
                        _mk_text_great_again(sep_boxes_before, box_coords, box)
                index= len(box_list)
                boxes_to_snip = index - nr_of_sep_boxes_before
                nr_of_sep_boxes_before = 0
                box_list = box_list[:boxes_to_snip]
                box_list = _add_to_box_list(new_text, start, end, box_list)
            if len(sep_boxes_after) > 0:
                new_text, nr_of_sep_boxes_after =\
                        _mk_text_great_again(sep_boxes_after, box_coords, box)
                box_list = _add_to_box_list(new_text, start, end, box_list)
        else:
            box_list = _add_to_box_list(box.text, start, end, box_list)

    #print('box_list in _mk_list_of_boxes')
    #for i, box in enumerate(box_list):
    #    print(i, box)

    return box_list


def _add_to_box_list(new_text, start, end, box_list):
    words = _prepare_text(new_text, start, end)
    if not words or words == []:
        pass
    else:
        text = ' '.join(w for w in words)
        box_list.append([text])

    return box_list


def _mk_text_great_again(sep_boxes, box_coords, box):
    '''
    The problem I'm facing here is that I need to tell the function that calls
    this one how many sep_boxes actually turned out to be accepted for correction.
    Not all will, that much is sure, but how do I count this?
    '''
    nr_of_gaps = 0
    new_text = list()
    oddies = _find_oddies(sep_boxes, box_coords)
    gaps = _mk_dict_of_gaps_in_lines(oddies, box_coords)
    for k, v in gaps.items():
        for _, vv in v.items():
            for kee in vv.keys():
                if kee == 'oddy':
                    nr_of_gaps += 1
    for line_to_correct, gap_dict in gaps.items():
        gaps, new_text = _fill_gaps(gaps, box, new_text)
        corrected_line = _correct_line(gaps, line_to_correct)
        index = line_to_correct - 1
        new_text.insert(index, corrected_line)
    #sys.exit()

    return new_text, nr_of_gaps


def _correct_line(gaps, line_to_correct):
    print('gaps, line_to_correct', gaps, line_to_correct)
    d = gaps[line_to_correct]
    best_fits = list()
    correct_line = list()
    for k, v in d.items():
        best_fits = sorted([bf for bf in v.keys() if bf != 'oddy' and bf > 0])
        for bf in best_fits:
            print('bf, v[bf]', bf, v[bf])
            if v[bf] in correct_line:
                continue
            else:
                correct_line.append(v[bf])
                if v['oddy']:
                    correct_line.append(v['oddy'])
                break
    correct_line = ' '.join(part for part in correct_line)
    print('corrected line', correct_line)

    return correct_line


def _could_be_box_w_missing_text(box):
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
    print('nr_of_lines_to_expect', nr_of_lines_to_expect, y_extension)

    text = box.text
    text_split_in_lines = text.split('\n')
    text_split_in_lines = list(filter(None, text_split_in_lines))
    nr_of_lines_in_fact = len(text_split_in_lines)
    print('nr_of_lines_in_fact', nr_of_lines_in_fact)

    if nr_of_lines_in_fact > nr_of_lines_to_expect:
        print('Found box where text could be missing')
        print('text.split("\\n"):')
        for i, line in enumerate(text_split_in_lines):
            print(i, line, len(line))
        return True

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
    box = boxes[i]
    sep_boxes = list()

    if after:
        boxes_after = boxes[i+1:]
        boxes_to_check = boxes_after
    elif before:
        boxes_before = reversed(boxes[:i])
        boxes_to_check = boxes_before

    token = True
    while token:
        for b_o_x in boxes_to_check:
            b_o_x_coords = _get_coords (b_o_x)
            if _is_inside_of_box(box_coords, b_o_x_coords):
                sep_boxes.append(b_o_x)
            else:
                token = False

    return sep_boxes


def _find_oddies(sep_boxes, box_coords):
    #print('_find_oddies ........................')
    x0, x1, y0, y1 = box_coords
    y_extension = y1 - y0
    nr_of_lines_to_expect = round(y_extension/11.8)
    oddies = dict()
    for j, sep_box in enumerate(sep_boxes):
        #print('sep_box', sep_box)
        c = round((sep_box.x0 - x0) / 4.9)
        for index in range(nr_of_lines_to_expect):
            line_nr = nr_of_lines_to_expect - index
            #print(line_nr, sep_box.y0, round(y0 + (index+0.4)*11.8), sep_box.y1)
            if sep_box.y0 <= round(y0 + (index+0.4)*11.8) <= sep_box.y1:
                try:
                    oddies[line_nr].append(sep_box)
                except KeyError:
                    oddies[line_nr] = list()
                    oddies[line_nr].append(sep_box)
                break

    return oddies


def _mk_dict_of_gaps_in_lines(oddies, box_coords):
    '''
    This function takes the fragmented text pieces that were found in "oddies"
    and calculates the gap that exists in front of the lost text fragment (or
    after if there is more than one "oddy").

    '''
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
                #print('gap, x0, box_coords', gap, lost_box.x0, box_coords)
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
            elif i > 0 and i == len(lost_boxes)-1:
                gap = lost_box.x0 - lost_boxes[i-1].x1
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
                gap = box_coords[1] - lost_box.x1
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = ''
            else:
                gap = lost_box.x0 - lost_boxes[i-1].x1
                gaps[k][gap] = dict()
                gaps[k][gap]['oddy'] = lost_text
        # Filtering with ext > 17 is based on the assumption that in German a word
        # must have two characters (like "zu", "an", "da") plus a space before and
        # after, which means 4*4.9 = 19.6 --> must be 18 at least
        gaps_keys = [kee for kee in gaps[k].keys()]
        for i, gap in enumerate(gaps_keys):
            if gap <= 17:
                kee = gaps_keys[i-1]
                gaps[k][kee]['oddy'] += ' ' + gaps[k][gap]['oddy']
                del gaps[k][gap]
                del gaps[k]

    #print('gaps in mk_dict_of_gaps_in_lines\n', gaps)
    return gaps


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
    quotes = ['\u201C', '\u201D', '\u201E', '\u201F', '\u2033', '\u2036', '\u0022']
    # puncts are sentence FINISHERS! It must be possible to have a new paragraph next.
    puncts = ['.', '!', '?']
    box_text = box.text.split('\n')
    box_text = list(filter(None, box_text))

    for i, line in enumerate(box_text):
        line = line.strip()
        print('i+1, line:', i+1, line)
        if not line:
            continue
        elif len(line) >= 40:
            new_text.append(line)
        elif line[-1] in puncts:
            new_text.append(line)
        elif line[-1] in quotes:
            if line[-2] in puncts:
                new_text.append(line)
        else:
            # counting of line_nr starts with 1
            #print('filling gaps, line, line_nr:', line, i+1)
            fragm_extension = round(len(line)*4.9)
            for k, v in gaps.items():
                #print('k, v, fragm_extension', k, v, fragm_extension)
                for kk, vv in v.items():
                    #print('kk, vv', kk, vv)
                    leftover = kk - fragm_extension
                    #print('leftover, line', leftover, line)
                    vv[leftover] = line

    print('gaps in _fill_gaps', gaps)
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
    exceptions = ['sen.', 'So.']
    for exc in exceptions:
        abbrevs.remove(exc)
    new_sentences = list()
    skip = False
    for i, sentence in enumerate(sentences):
        if not skip:
            new_sentence = ''
        else:
            skip = False
            continue
        words = sentence.split(' ')
        words = list(filter(None, words))
        last_word = words[-1].strip()
        if last_word in abbrevs:
            try:
                next_sent = sentences[i+1]
                next_words = next_sent.split(' ')
                next_words = list(filter(None, next_words))
                next_first_word = next_words[0].strip()
            except IndexError:
                print(sentences)
                print('the culprit:', last_word)
                raise Exception('Why is there an abbrevation but nothing follows?')

            if next_first_word in abbrevs:
                # sentence needs to continue without empty space
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
        else:
            new_sentence += sentence
            new_sentence = re.sub(' +', ' ', new_sentence)
            new_sentences.append(new_sentence)

    return new_sentences


def _save_the_contributions(legislature, key, protocol_nr, start_end, sentences):
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
        dir_loc = f'/home/sam/projects/vEnvs/parli_NRW/parli_NRW/data/WP{legislature}/'
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
        dir_loc = './parli_data/wf15_dilled_wps/'
        os.makedirs(dir_loc, exist_ok=True)

        file_loc = dir_loc + 'WP_{}.dill'.format(legislature)
        with open(file_loc, 'wb') as fout:
            dill.dump(wp, fout)

        print(f'Reset of contribution {k} at position {start_end}')


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
    box_list = list()
    token_speaks = False
    is_question = False
    _break = False

    for page in pages:
        for _, vv in page.items():          # _: header, columns
            print('kind:', kind)
            if _break:
                _break = False
                break
            elif 'Fr' in kind and is_question:
                print('Fr in kind:', ('Fr' in kind))
                print('is_question:', is_question)
                is_question = False
                #break
                return box_list
            for i, box in enumerate(vv):    # vv: list with boxes
                #print(f'{i} token_speaks:{token_speaks}')
                #print('.', box)
                box_text = _prepare_text(box.text, start, end, applause=True)
                #print('..', box_text)
                if _has_no_text(box_text):
                    continue
                elif kind == 'speech':
                    if not token_speaks and _is_speaker(box_text, mdl, start, end):
                        box_list.append(box)
                        token_speaks = True
                    elif token_speaks:
                        if _is_president(box_text, start, end):
                            token_speaks = False
                            sent = box_list[-1].text
                            applause = True
                            sent = _prepare_text(sent, start, end, applause)
                            #print(box_list, sent)
                            if sent:
                                if  _contains_final_words(sent):
                                    _break = True
                                    break
                                elif _ends_with_applause(sent):
                                    _break = True
                                    break
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
                    if not token_speaks and _is_speaker(box_text, mdl, start, end):
                        box_list.append(box)
                        token_speaks = True
                        if _is_question(box_text, start, end):
                            is_question = True
                    elif token_speaks:
                        if 'Fr' in kind and _is_president(box_text, start, end):
                            token_speaks = False
                            if is_question:
                                #print('box_list before break')
                                break
                            else:
                                continue
                        elif _is_president(box_text, start, end):
                            token_speaks = False
                            continue
                        elif _is_other_MdL(box_text, mdl, first_names, last_names,\
                                start, end):
                            token_speaks = False
                            break
                        else:
                            box_list.append(box)
                    else:
                        continue

    #print('box_list in _find_boxes_with_speech:')
    #print(box_list)
    return box_list


def _find_pages_of_interest(boxes, start, end):
    page_of_interest = False
    pages = list()
    for page_nr, page in boxes.items():     # pagenr counted from 1
        print('internal pagenr: ', page_nr)
        print('start, end: ', start, end)
        for kk, vv in page.items():         # page: dict with header, left and right col
            for box in vv:
                if _is_page_of_interest(box, start, end, page_of_interest):
                    page_of_interest = True
                    pages.append(page)

    return pages


def _is_page_of_interest(box, start, end, page_of_interest):
    try:
        words = box.text.split(' ')
    except AttributeError:
        return False
    words = list(filter(None, words))
    for word in words:
        word = word.strip()
        word = re.sub('[!,*\n]', '', word)
        word = word.strip()
        if word.isdigit():
            if not page_of_interest:
                if int(start) == int(word):
                    page_of_interest = True
                    return page_of_interest
            elif page_of_interest:
                if int(start) < int(word) <= int(end):
                    return page_of_interest
                elif int(word) == int(end)+1:
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
            print('sents---------------->', sents)
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
    first_name = _low_cap_all(mdl.first_name)
    last_name = _low_cap_all(mdl.last_name)
    found_first_name = False

    #words = _prepare_text(box_text, start, end)
    #print('words', words)

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
    first_word = re.sub(clutter, '', first_element)
    #print('first_word in _is_speaker', first_word, first_name)

    if first_names:
        counter = 0
        while counter < l_fn:
            if first_word in first_names:
                words = words[1:]
                words = _cut_off_peertitle(words)
                first_element = words[0]
                first_word = re.sub(clutter, '', first_element)
                found_first_name = True
                break
            else:
                counter += 1
                words = words[1:]
                if words != []:
                    words = _cut_off_peertitle(words)
                    first_element = words[0]
                    first_word = re.sub(clutter, '', first_element)
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
                print('found MdL: is_speaker', first_name, last_name)
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

    words = _prepare_text(box_text, start, end)
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

    words = _prepare_text(box_text, start, end)
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
    first_element = words[0]
    first_word = re.sub(clutter, '', first_element)
    while True:
        if first_word.upper() in vN_list:
            names_to_check.append(first_word)
            words = words[1:]
            if words is None:
                break
            first_element = words[0]
            first_word = re.sub(clutter, '', first_element)
        else:
            break

    if names_to_check:
        words = _cut_off_peertitle(words)
        if first_word.upper() in nN_list:
            if first_word.upper() != last_name:
                print('Found other MdL')
                return True
    else:
        return False


def _prepare_text(box_text, start, end, applause=False):
    '''
    Will look for text that belongs into the header and take it out
        --> clean_box_text
    Will look for remarks having a pattern like this:
        (Name of MdL [party]: some remark)
        Since this can contain line breaks as well as remarks from other MdLs
        I reduced the pattern to this:
            (anything linebreaks anything)
    Finally the text is scanned for academic titles which will be removed.

    Returns a list of words
    '''

    parties = ['(GRÜNE)', '(SPD)', '(CDU)', '(FDP)', '(PIRATEN)', '(AfD)']
    clean_box_text = _text_without_header_items(box_text, start, end)
    if not clean_box_text:
        return None

    #print('clean_box_text before\n', clean_box_text)
    if applause:
        words = clean_box_text.split(' ')
        words = list(filter(None, words))
        if '(Beifall' in words:
            words = [w for w in words if w != '\n']
            return words

    remark_pattern1 = re.compile('\(.*\n*.*\n*.*\)')
    remark_pattern2 = re.compile('\((Beifall|Zuruf) .*\)')
    remark_patterns = [remark_pattern1, remark_pattern2]

    for remark_pattern in remark_patterns:
        m = re.search(remark_pattern, clean_box_text)
        if m:
            pattern = m[0]
            #print('pattern', pattern)
            if pattern in parties:
                pass
            else:
                clean_box_text = clean_box_text.replace(pattern, '')
    if applause:
    #    print('clean_box_text after\n', clean_box_text)
        pass
    words = clean_box_text.split(' ')
    words = list(filter(None, words))
    words = [w for w in words if w != '\n']
    if words == []:
        return None
    #words = _cut_off_akad_titel(words)

    return words


def _cut_off_akad_titel(words):
    acad_titles = ['Dr.', 'Prof.', 'Dr.Dr.', 'Prof.Dr.']
    first_word = words[0]
    while first_word in acad_titles:
        words = words[1:]
        first_word = words[0]
    return words


def _cut_off_peertitle(words):
    peer_titles = ['von', 'van', 'zur', 'auf', 'de', 'der', 'Freifrau', 'Freiherr',\
            'Gräfin', 'Graf', 'vom']
    first_word = words[0]
    while first_word in peer_titles:
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
    box_list = list()
    for i, box in enumerate(box_list_to_iterate):
        box_text = box[0]
        #print(i, box_text)
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

    #words = _prepare_text(box_text, start, end)
    words = box_text
    if not words:
        return False

    last_element = words[-1]
    if last_element[-1] == '?':
        print('Found question')
        #print(words)
        return True
    else:
        return False


def _get_rid_of_line_breaks_wth_hyphens(sents, mdl_names):
    #print('_get_rid_of_line_breaks_with_hyphens\n', sents)
    new_sentences = list()
    for j, sent in enumerate(sents):
        skip = False
        new_sentence = ''
        if '-\n' in sent:
            parts = sent.split('-\n')
        else:
            new_sentences.append(sent)
            continue
        for i, part in enumerate(parts):
            words = part.split(' ')
            words = list(filter(None, words))
            if words:
                last_word = words[-1].strip()
            else:
                continue

            if skip:
                skip = False
                continue
            try:
                next_part = parts[i+1]
                next_words = next_part.split(' ')
                next_words = list(filter(None, next_words))
                first_word = next_words[0].strip()
                last_char = first_word[-1]
                new_word = last_word + first_word
                new_word = re.sub(clutter, '', new_word)
                new_word = _find_correct_spelling(new_word, mdl_names,\
                    last_word, first_word, name='get_rid_of_line_breaks_with_hyphens')
                if not last_char.isalnum():
                    if not new_word[-1].isalnum():
                        pass
                    else:
                        new_word += last_char
                        #print('+'*10)
                        #print('added last char in _get_rid_of_line_bre...', new_word)
                combined_parts = words[:-1] + [new_word] + next_words[1:]
                new_part = ' '.join(w for w in combined_parts)
                new_sentence += new_part
                skip = True
            except IndexError:
                part = part.strip()
                new_sentence += part

        if new_sentence[-1] not in ['.', '!', '?', ':']:
            new_sentence += '.'
        #print('new_sentence in _get_rid_of_line_breaks_with_hyphens\n', new_sentence)
        new_sentences.append(new_sentence)

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

    for i, sentence in enumerate(sents):
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
                print('last word: ', last_word)
                raise Exception('Sentence ends with hyphen but there is no second part to that word!')
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
                    print('last word: ', word)
                    raise Exception('Sentence ends with hyphen but there is no second part to that word!')
                without_hyphen = word[:-1] + next_word
                if without_hyphen[-1].isalpha():
                    new_word = without_hyphen
                else:
                    new_word = without_hyphen[:-1]
                    take_punctuation_mark = True
                new_word = _find_correct_spelling(new_word, mdl_names, word,\
                        next_word, name='_find_words_sep_by_hyphens')
                print('new_word (aka without_hyphen)', new_word)
                if take_punctuation_mark:
                    take_punctuation_mark = False
                    new_word = without_hyphen
                new_words += [new_word]
                skip = True
                print('new_words', new_words)
            else:
                new_words += [word]
        new_sentence = ' '.join(w for w in new_words)
        #print('final sentence after getting rid of hyphens\n', new_sentence)
        sentences.append(new_sentence)

    return sentences


def _find_last_remarks(sents):
    skip = False
    sentences = list()

    for i, sent in enumerate(sents):
        if skip:
            skip = False
            continue
        elif sent[0] == '(':
            try:
                next_sent = sents[i+1]
                if next_sent[-1] == ')':
                    skip = True
                    print(f'****** skipped ******\n{sent}\n{next_sent}')
                    print()
            except IndexError:
                sentences.append(sent)
                continue
        else:
            sentences.append(sent)

    return sentences


def _find_final_phrase(sents):
    skip = False
    sentences = list()

    for i, sent in enumerate(sents):
        if skip:
            skip = False
            continue
        elif _contains_final_words(sent):
            try:
                next_sent = sents[i+1]
                print(f'Houston! We have a problem!\n{sent}\n{next_sent}')
                skip, corrected_text = _correct_PDF_blunder(sent, next_sent)
                if skip:
                    sentences.append(corrected_text)
                else:
                    sent = sents[i-1]
                    skip, corrected_text = _correct_PDF_blunder(sent, next_sent)
                    if skip:
                        sentences.append(corrected_text)
                        sentences.append(sents[i])
                        del sentences[i-1]
                    else:
                        print('Could not match, will be left as is.')
                        sent = sents[i]
                        sentences.append(sent)
            except IndexError:
                sentences.append(sent)
                continue
        else:
            sentences.append(sent)

    return sentences


def _contains_final_words(sent):
    #print('sent in _contains_final_words\n', sent)
    try:
        words = sent.split(' ')
    except AttributeError:
        words = sent

    if 'danke' and 'Ihnen' and 'Aufmerksamkeit.' in words:
        return True
    elif 'Dank' and 'Aufmerksamkeit.' in words:
        return True
    elif 'Vielen' and 'Dank.' in words:
        return True
    elif 'Herzlichen' and 'Dank.' in words:
        return True
    elif words[0] == 'Danke.':
        return True
    elif 'danke' and 'Ihnen.' in words:
        return True
    elif 'Schönen' and 'Dank.' in words:
        return True
    return False


def _ends_with_applause(sent):
    try:
        words = sent.split(' ')
    except AttributeError:
        words = sent

    if '(Beifall' in words:
        #print('sent in _ends_with_applause\n', sent)
        #print('*'*70)
        return True
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
        new_word = last_word + first_word       # last_word still contains hyphen!
        new_word = re.sub(clutter, '', new_word)
        with_hyphen = re.sub(clutter, '', last_word + first_word)
        without_hyphen = re.sub(clutter, '', last_word[:-1] + first_word)
        with_space = last_word + ' ' + first_word
        with_2_spaces = last_word[:-1] + ' - ' + first_word
        if new_word in hyphened_words:
            return new_word
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
        elif with_2_spaces in german_words:
            return with_2_spaces
        elif with_2_spaces in hyphened_words:
            return with_2_spaces
        # found neither with nor without hyphen
        else:
            #with_space = last_word + ' ' + first_word
            #with_2_spaces = last_word[:-1] + ' - ' + first_word
            print(f'1: {with_hyphen}, 2: {without_hyphen}, 3: {with_space}, 4: {with_2_spaces}')
            choose = input('1, 2, 3, 4 or . if correction: ')
            if choose == '1':
                _save_with_hyphen(with_hyphen)
                return with_hyphen
            elif choose == '2':
                _save_without_hyphen(without_hyphen)
                return without_hyphen
            elif choose == '3':
                return with_space
            elif choose == '4':
                return with_2_spaces
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


def _save_with_hyphen(new_word_with_hyphen):
    with open('./parli_data/new_hyphened_words.txt', 'a',\
            encoding='utf-8') as fout:
        fout.write('\n')
        fout.write(new_word_with_hyphen)


def _save_without_hyphen(word_without_hyphen):
    with open('./parli_data/new_german_words.txt', 'a',\
            encoding='utf-8') as fout:
        fout.write('\n')
        fout.write(word_without_hyphen)


def _get_rid_of_remarks_within_box(boxes):
    box_list = list()
    for j, box in enumerate(boxes):
        box_text = box[0]
        try:
            box_text = box_text.strip()
        except AttributeError:
            box_text = box_text[0].strip()

        if _is_remark_leftover(box_text):
            continue

        new_text = ''
        lines = box_text.split('\n')
        l = len(lines)
        for i in range(l):
            line = lines[i]
            line = line.strip()
            #print('line:', line)
            try:
                if line[0] == '(' and line[-1] == ')':
                    continue
                else:
                    if i+1 < l:
                        new_text += ' ' + line + '\n'
                    else:
                        new_text += ' ' + line
            except IndexError:
                pass
        box_list.append([new_text])

    return box_list


def _is_remark_leftover(box):
    first_word = box[0].split(' ')[0]
    if first_word[0] == '[':
        if first_word[-1] == ':' and first_word[-2] == ']':
            return True
    return False


def _connect_boxes(box_list_to_iterate, german_words, mdl_names):
    '''
    Connects all boxes to one single text block.
    I consider only two cases:
        - There is a hyphen at the end of the last word of a box
            --> will that be one word with first word of next box?
        - Otherwise just connect boxes with a space in between.
    '''

    skip = False
    complete_text = ''

    for i, box in enumerate(box_list_to_iterate):
        #print('connecting boxes', i, box)
        if skip:
            skip = False
            continue
        if box == []:
            continue
        box_text = box[0].strip()
        try:
            next_box = box_list_to_iterate[i+1]
        except IndexError:
            complete_text += ' ' + box_text
            continue
        if next_box == []:
            complete_text += ' ' + box_text
            continue
        words = box_text.split(' ')
        words = list(filter(None, words))
        next_box_text = next_box[0].strip()
        next_words = next_box_text.split(' ')
        next_words = list(filter(None, next_words))
        if not box_text:
            continue
        elif box_text[-1] == '-':
            last_word = words[-1].strip()[:-1]
            first_word = next_words[0].strip()
            last_char = first_word[-1]
            new_word = last_word + first_word
            new_word = re.sub(clutter, '', new_word)
            new_word = _find_correct_spelling(new_word, mdl_names,\
                    last_word, first_word, name='_connect_boxes')
            if not last_char.isalnum():
                new_word += last_char
            combined_boxes = words[:-1] + [new_word] + next_words[1:]
            combined_box_text = ' '.join(w for w in combined_boxes)
            complete_text += ' ' + combined_box_text
            skip = True
        else:
            complete_text += ' ' + box_text

    #print(complete_text)
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
        print(i, box)
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
            box_text = box_text.split('):')[1:]
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


def _open_dilled_wp(legislature):
    '''
    '''
    try:
        dir_ = f'/home/sam/projects/vEnvs/parli_NRW/parli_NRW/data/WP{legislature}/'
        latest_file = dir_ + sorted(os.listdir(dir_))[-1]
        print(f'opening: {latest_file}')
        with open(latest_file, 'rb') as fin:
            wp = dill.load(fin)
    except FileNotFoundError:
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

    return wp


if __name__ == '__main__':
    wf15_convert_PDF2text_and_save()
