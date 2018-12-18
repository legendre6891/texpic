from bs4 import BeautifulSoup

from texpic import *

def mathify(htmlfile):
    with open(htmlfile, 'r') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')

    display_divs = soup.find_all('div', class_='displayed-math')
    displays = [div.contents[0] for div in display_divs]
    pictures = draw_equations(displays)

    for i, (div, pic_info) in enumerate(zip(display_divs, pictures)):
        png_bytes, width, height, align = pic_info

        with open('AAAA-{}.png'.format(i), 'wb') as f:
            f.write(png_bytes)

        tag = soup.new_tag('img',
                width=width,
                height=height,
                style="vertical-align: {}px;".format(align),
                src='AAAA-{}.png'.format(i))

        div.string = ''
        div.append(tag)




    display_divs = soup.find_all('span', class_='inline-math')
    displays = ['$' + div.contents[0] + '$' for div in display_divs]
    pictures = draw_equations(displays)

    for i, (div, pic_info) in enumerate(zip(display_divs, pictures)):
        png_bytes, width, height, align = pic_info

        with open('BBBB-{}.png'.format(i), 'wb') as f:
            f.write(png_bytes)

        tag = soup.new_tag('img',
                width=width,
                height=height,
                style="vertical-align: {}px;".format(align),
                src='BBBB-{}.png'.format(i))

        div.string = ''
        div.append(tag)

    print(soup.prettify())



mathify('test.html')
