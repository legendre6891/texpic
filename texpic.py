import math
from subprocess import DEVNULL, check_output

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


def make_png(orig, depth):
    # Input:
    #   fname - filename of the pnm file.
    #   depth and pagemargin are read from the logfile

    # normalize depth first (old name: tex_point_normalization)
    RENDER_OVERSAMPLE = 5
    DISPLAY_OVERSAMPLE = 5
    OVERSAMPLE = RENDER_OVERSAMPLE * DISPLAY_OVERSAMPLE

    FONT_SCALE = 1
    SCREEN_DPI = 96

    DPI = SCREEN_DPI * FONT_SCALE * 72.27 / 72 * OVERSAMPLE


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

    padded = check_output(['pnmpad', '-white', '-bottom={}'.format(bottom_padding),
        '-top={}'.format(top_padding), '-left={}'.format(left_padding),
        '-right={}'.format(right_padding)],
                   input = cropped)

    padded_width, padded_height = pnm_dimensions(padded)

    final_width = padded_width // RENDER_OVERSAMPLE
    final_height = padded_height // RENDER_OVERSAMPLE

    p1 = check_output('ppmtopgm', input=padded)
    p2 = check_output(['pamscale', '-reduce', '{}'.format(RENDER_OVERSAMPLE)],
            input=p1, stderr=DEVNULL)
    p3 = check_output(['pnmgamma', '.3'], input=p2)
    png = check_output(['pnmtopng', '-compression', '9'],
                          input=p3)

    # finally, the convesion to html
    html_width = final_width // DISPLAY_OVERSAMPLE
    html_height = final_height // DISPLAY_OVERSAMPLE
    vertical_align = -depth_padded // OVERSAMPLE

    return png, html_width, html_height, vertical_align

__all__ = ['make_png']

