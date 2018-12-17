import math
import tempfile
import subprocess
import os
from subprocess import DEVNULL, check_output


from split_pnm_stream import split_pnm_stream

RENDER_OVERSAMPLE = 5
DISPLAY_OVERSAMPLE = 5
OVERSAMPLE = RENDER_OVERSAMPLE * DISPLAY_OVERSAMPLE

FONT_SCALE = 1
SCREEN_DPI = 96

DPI = SCREEN_DPI * FONT_SCALE * 72.27 / 72 * OVERSAMPLE

def round_up(x, b):
    return int(math.ceil(x / b)) * b


def pnm_dimensions(stream):
    i = 0

    # skip to, and then over, the first newline
    while stream[i] != 10:
        i += 1
    i += 1

    while True:
        # Skip over all comment characters
        if stream[i] != 35:
            break

        while stream[i] != 10:
            i += 1
        i += 1

    j = i

    while stream[j] != 10:
        j += 1

    x = stream[i:j].decode('ascii')

    w, h = (int(z) for z in x.split())
    return w, h


def normalize_pnm(orig, depth):
    # Input:
    #   fname - filename of the pnm file.
    #   depth and pagemargin are read from the logfile

    # normalize depth first (old name: tex_point_normalization)

    depth = depth * DPI / 72.27

    w, h = pnm_dimensions(orig)

    bottom_cropped = check_output(['pnmcrop', '-white', '-bottom'], input=orig)
    wb, hb = pnm_dimensions(bottom_cropped)
    bottom_crop = h - hb

    cropped = check_output(['pnmcrop', '-white'], input=bottom_cropped)
    wc, hc = pnm_dimensions(cropped)
    top_crop = hb - hc

    # calculate bottom padding
    snippet_depth = round(depth) - bottom_crop
    depth_padded = round_up(snippet_depth, OVERSAMPLE)
    depth_increment = depth_padded - snippet_depth
    bottom_padding = depth_increment

    # calculate top padding
    height_padded = round_up(hc + bottom_padding, OVERSAMPLE)
    top_padding = height_padded - (hc + bottom_padding)

    # calculate left and right padding, and distribute evenly
    width_padded = round_up(wc, OVERSAMPLE)
    left_padding = int((width_padded - wc) / 2)
    right_padding = width_padded - wc - left_padding

    padded = check_output([
        'pnmpad', '-white', '-bottom={}'.format(bottom_padding),
        '-top={}'.format(top_padding), '-left={}'.format(left_padding),
        '-right={}'.format(right_padding)
    ],
                          input=cropped)

    padded_width, padded_height = pnm_dimensions(padded)

    final_width = padded_width // RENDER_OVERSAMPLE
    final_height = padded_height // RENDER_OVERSAMPLE

    p1 = check_output('ppmtopgm', input=padded)
    p2 = check_output(['pamscale', '-reduce', '{}'.format(RENDER_OVERSAMPLE)],
                      input=p1,
                      stderr=DEVNULL)
    p3 = check_output(['pnmgamma', '.3'], input=p2)
    png = check_output(['pnmtopng', '-compression', '9'], input=p3)

    # finally, the convesion to html
    html_width = final_width // DISPLAY_OVERSAMPLE
    html_height = final_height // DISPLAY_OVERSAMPLE
    vertical_align = -depth_padded // OVERSAMPLE

    return png, html_width, html_height, vertical_align


def parse_log_file(logfile):
    # Find all lines in the log file that start with
    # the string \vbox. It should read something like this
    # \vbox(58.95143+0.0)x345.0
    #
    # We want to extract the depth, which is 0.0 in this case.

    depths = []

    with open(logfile, 'rb') as f:
        for line in f:
            line = line.decode(errors='ignore').strip()
            if line.startswith('\\vbox('):
                a = line.find('+')
                b = line.find(')')
                depths.append(float(line[a + 1:b]))

    return depths


def split_pnm_stream2(stream):
    indices = []

    for i in range(len(stream) - 1):
        if stream[i] == 80 and stream[i+1] == 53:
            indices.append(i)

    return indices

def make_pnm(latexfile):
    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.run(['pdflatex', '--interaction=batchmode',
            '-output-directory', tmpdirname, latexfile],
                       stderr=DEVNULL,
                       stdout=DEVNULL)
        subprocess.run(['pdflatex', '--interaction=batchmode',
            '-output-directory', tmpdirname, latexfile],
                       stderr=DEVNULL,
                       stdout=DEVNULL)
        
        filename = os.path.basename(latexfile)
        if filename.endswith('.tex'):
            basename = os.path.join(tmpdirname, filename[:-4])
        else:
            basename = os.path.join(tmpdirname, filename)

        pdffile = basename + '.pdf'
        logfile = basename + '.log'

        depths = parse_log_file(logfile)


        x = check_output(['gs',
            '-q', '-dNOPAUSE', '-dBATCH',
            '-dTextAlphaBits=4',
            '-dGraphicsAlphaBits=4',
            '-r{}'.format(DPI), '-sDEVICE=pnmraw',
            '-sOutputFile=-',
            pdffile])

        splits = split_pnm_stream(x, len(depths))

        pics = []
        for i in range(len(splits) - 1):
            pics.append(x[splits[i]:splits[i+1]])

        pics.append(x[splits[-1]:])

        return pics, depths



def draw_equations(equations):
    f = tempfile.NamedTemporaryFile(mode='w', delete=False)

    template = r'''\documentclass[13pt]{scrartcl}
\usepackage[fleqn, leqno]{amsmath}
\usepackage{newtxtext}
\usepackage{newtxmath}
\usepackage[active,textmath,displaymath,tightpage,showbox]{preview}
'''
    print(template, file=f)

    print(r'\begin{document}', file=f)
    for eq in equations:
        print(eq, file=f)
        print('', file=f)
    print(r'\end{document}', file=f)

    f.close()

    pics, depths = make_pnm(f.name)

    pngs = []
    for pic, depth in zip(pics, depths):
        pngs.append(normalize_pnm(pic, depth))

    
    return pngs



equations = ['$a + b = 4$', '$x^2 + y^2 = z^2']



__all__ = ['normalize_pnm', 'make_pnm']
