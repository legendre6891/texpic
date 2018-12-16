#!/usr/bin/python3

from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile

import subprocess
from subprocess import PIPE, DEVNULL

import os

import math

CONSTANTS = {
    'render_oversample': 5,
    'display_oversample': 5,
    'font_scale': 1,
    'screen_dpi': 96,
}
CONSTANTS['oversample'] = CONSTANTS['render_oversample'] * CONSTANTS[
    'display_oversample']
CONSTANTS['dpi'] = CONSTANTS['screen_dpi'] * CONSTANTS[
    'font_scale'] * 72.27 / 72 * CONSTANTS['oversample']


def filename_no_ext(path):
    return os.path.splitext(path)[0]


def tex_point_normalization(x):
    return x / 72.27 * CONSTANTS['dpi']


def round_up(x, b):
    return int(math.ceil(x / b)) * b


def pnm_dimensions(fname):
    with open(fname, 'rb') as f:
        # skip over the first line
        f.readline()

        # skip over comments
        for line in f:

            # skip anything with a pound sign
            if line[0] != 35:
                break

        line = line.decode('utf-8').strip()

        w, h = (int(x) for x in line.split())
        return w, h


def normalize_pnm(fname, depth, pagemargin=0):
    # Input:
    #   fname - filename of the pnm file.
    #   dimensiosn - a dictionary with entries:
    #       ...
    #       ...

    basename = filename_no_ext(fname)
    w, h = pnm_dimensions(fname)

    bottomcrop_fname = basename + '.bottomcrop.pnm'

    with open(bottomcrop_fname, 'wb') as f, open(fname, 'r') as orig:
        subprocess.run(['pnmcrop', '-white', '-bottom'], stdin=orig, stdout=f)

    wb, hb = pnm_dimensions(bottomcrop_fname)
    bottom_crop = h - hb

    crop_fname = basename + '.topcrop.pnm'
    with open(crop_fname, 'wb') as f, open(bottomcrop_fname, 'r') as orig:
        subprocess.run(['pnmcrop', '-white'], stdin=orig, stdout=f)

    wc, hc = pnm_dimensions(crop_fname)
    top_crop = hb - hc

    # calculate bottom padding
    snippet_depth = round(depth + pagemargin) - bottom_crop
    depth_padded = round_up(snippet_depth, CONSTANTS['oversample'])
    depth_increment = depth_padded - snippet_depth
    bottom_padding = depth_increment

    # calculate top padding
    height_padded = round_up(hc + bottom_padding, CONSTANTS['oversample'])
    top_padding = height_padded - (hc + bottom_padding)

    # calculate left and right padding, and distribute evenly
    width_padded = round_up(wc, CONSTANTS['oversample'])
    left_padding = int((width_padded - wc) / 2)
    right_padding = width_padded - wc - left_padding

    padded_fname = basename + '.padded.pnm'
    with open(padded_fname, 'wb') as f, open(crop_fname, 'r') as orig:
        subprocess.run([
            'pnmpad', '-white', '-bottom={}'.format(bottom_padding),
            '-top={}'.format(top_padding), '-left={}'.format(left_padding),
            '-right={}'.format(right_padding)
        ],
                       stdin=orig,
                       stdout=f)

    padded_width, padded_height = pnm_dimensions(padded_fname)

    final_width = padded_width // CONSTANTS['render_oversample']
    final_height = padded_height // CONSTANTS['render_oversample']

    png_fname = basename + '.png'
    with open(png_fname, 'wb') as f, open(padded_fname, 'r') as orig:
        p1 = subprocess.Popen('ppmtopgm', stdin=orig, stdout=PIPE)
        p2 = subprocess.Popen([
            'pamscale', '-reduce', '{}'.format(CONSTANTS['render_oversample'])
        ],
                              stdin=p1.stdout,
                              stdout=PIPE,
                              stderr=DEVNULL)
        p3 = subprocess.Popen(['pnmgamma', '.3'], stdin=p2.stdout, stdout=PIPE)
        p4 = subprocess.Popen(['pnmtopng', '-compression=9'],
                              stdin=p3.stdout,
                              stdout=f)

    # finally, the convesion to html

    html_width = final_width // CONSTANTS['display_oversample']
    html_height = final_height // CONSTANTS['display_oversample']
    vertical_align = -depth_padded // CONSTANTS['oversample']

    return html_width, html_height, vertical_align

    # cleanup
    for name in [bottomcrop_fname, crop_fname, padded_fname]:
        try:
            os.remove(name)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    return html_width, html_height, vertical_align

def parse_log_file(fname):
    # Find all lines in the log file that start with
    # the string \vbox. It should read something like this
    # \vbox(58.95143+0.0)x345.0
    #
    # We want to extract the depth, which is 0.0 in this case.

    depths = []

    with open(fname, 'rb') as f:
        for line in f:
            line = line.decode(errors='ignore').strip()
            if line.startswith('\\vbox('):
                a = line.find('+')
                b = line.find(')')
                depths.append(float(line[a + 1:b]))

    return depths


def latex_to_png(fname):
    basename = filename_no_ext(fname)

    subprocess.run(['pdflatex', '--interaction=batchmode', fname],
                   stderr=DEVNULL,
                   stdout=DEVNULL)
    subprocess.run(['pdflatex', '--interaction=batchmode', fname],
                   stderr=DEVNULL,
                   stdout=DEVNULL)

    subprocess.run([
        'gs', '-q', '-dNOPAUSE', '-dBATCH', '-dTextAlphaBits=4',
        '-dGraphicsAlphaBits=4', '-r{}'.format(
            CONSTANTS['dpi']), '-sDEVICE=pnmraw',
        '-sOutputFile={}-%d.pnm'.format(basename), basename + '.pdf'
    ])

    depths = parse_log_file(basename + '.log')

    outputs = []
    for i, d in enumerate(depths):
        w, h, align = normalize_pnm('{}-{}.pnm'.format(basename, i + 1),
            tex_point_normalization(d),
            pagemargin=0)

        outputs.append((w, h, align))

    # cleanup
    for ext in ['.pdf', '.aux', '.log']:
        try:
            os.remove(basename + ext)
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))

    try:
        os.remove(fname)
    except OSError as e:
        print("Error: %s - %s." % (e.filename, e.strerror))

    for i, _ in enumerate(depths):
        try:
            os.remove('{}-{}.pnm'.format(basename, i + 1))
        except OSError as e:
            print("Error: %s - %s." % (e.filename, e.strerror))


    return fname, outputs


def populate_template(soup, template):
    # Inputs:
    #	soup: a BeautifulSoup object
    #	template: string containing the preamble
    #
    # Output:
    #   filename, and list of math nodes

    displaymaths = soup.find_all('div', class_='displayed-math')
    inlines = soup.find_all('span', class_='inline-math')

    for m in displaymaths:
        print(m.contents[0])


    for m in inlines:
        print(m.contents[0])


    for inline in inlines:
        snippet = create_inline_snippet(content = m.content[0])


    return


    for m in maths:
        content = m.content[0]
        print(m.contents[0])

    return None, None

    f = NamedTemporaryFile(mode='w', delete=False, dir='.')

    print(template, file=f)

    print(r'\begin{document}', file=f)
    for m in maths:
        print(m.contents[0], file=f)
        print('', file=f)
    print(r'\end{document}', file=f)

    f.close()

    return f.name, maths


def main(soup, template):
    texfile, maths = populate_template(soup, template)
    return
    fname, outputs = latex_to_png(texfile)

    basename = os.path.basename(fname)

    for i, m in enumerate(maths):
        w, h, align = outputs[i]
        m.string = ''
        tag = soup.new_tag('img', width=w, height=h, style="vertical-align: {}px;".format(align), src='{}-{}.png'.format(basename, i+1))
        m.append(tag)

    print(soup.prettify())


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('html', type=argparse.FileType('r'))
    parser.add_argument('--template', dest='template', type=argparse.FileType('r'))
    parser.add_argument('--directory', dest='dir', type=str)
    args = parser.parse_args()

    html = args.html.read()
    args.html.close()

    # soup = BeautifulSoup(html, 'html.parser')
    soup = BeautifulSoup(html, 'lxml')
    template = args.template.read()

    main(soup, template)
