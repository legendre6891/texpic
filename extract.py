#!/usr/bin/python3

from bs4 import BeautifulSoup
from tempfile import NamedTemporaryFile

import subprocess
from subprocess import PIPE, DEVNULL

import os

import math


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
