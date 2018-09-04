#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "Holger Bast"
__email__ = "holgerbast at gmx de"
__copyright__ = "Copyright 2018"
__license__ = "MIT"
__version__ = "0"
__status__ = "Development"

import random
import hashlib
import numpy
from PIL import Image
from faker import Faker
from lxml import etree
from lxml.builder import E
from progressbar import progressbar

out = './example/'  # export folder for images and xml files

STRUCTURE_DEPTH = 5
MAXCNT_CHAPTER = 5
MAXCNT_SECTION = 5
MAXCNT_PARAGRAPH = 3
MAXCNT_IMAGE = 6
MAXCNT_IMAGELINK = 1000

fake = Faker(locale="de_DE")


def gen_heading_name():
    global fake
    return fake.sentence(nb_words=5).replace('.', '')


def gen_paragraph_text():
    global fake
    return fake.text()


def gen_paragraph(parent):
    for i in range(random.randint(1, MAXCNT_PARAGRAPH)):
        paragraph = E.para(gen_paragraph_text())
        parent.append(paragraph)

    return


def gen_section(parent, depth):
    if depth >= STRUCTURE_DEPTH:
        return

    for i in range(random.randint(1, MAXCNT_SECTION)):
        section = E.section(
            E.title(gen_heading_name())
        )
        parent.append(section)
        gen_paragraph(section)
        gen_section(section, depth+1)

    return


# DocBook Namespaces
ns0_NAMESPACE="http://docbook.org/ns/docbook"
ns0 = "{%s}" % ns0_NAMESPACE
ns1_NAMESPACE="http://www.w3.org/1999/xlink"  # xlink
ns1 = "{%s}" % ns1_NAMESPACE
ns2_NAMESPACE="http://www.w3.org/2001/XInclude"  # xi
ns2 = "{%s}" % ns2_NAMESPACE

NSMAP = {None: ns0_NAMESPACE, 'xlink': ns1_NAMESPACE, 'xi': ns2_NAMESPACE}

print('DocBook Dummy Document Generator')
print('--------------------------------')

# Generate Root-Element
document = etree.Element(ns0 + "book", nsmap=NSMAP)

# Generate Document-Structure
for i in progressbar(range(0, MAXCNT_CHAPTER), prefix='Document Structure: '):
    chapter = E.chapter(
        E.title(gen_heading_name())
    )
    # print(etree.tostring(chapter, pretty_print=True, method='xml', encoding=str))
    document.append(chapter)
    gen_section(chapter, 0)


# Adding Images
paragraphs = document.xpath('//para')
images = []

# for para in random.sample(range(0, len(paragraphs)-1), MAXCNT_IMAGE):
for para in progressbar(random.sample(range(0, len(paragraphs)-1), MAXCNT_IMAGE), prefix='Images: '):
    image_id = hashlib.md5(str(para).encode('utf-8')).hexdigest()
    rgb_array = numpy.random.rand(200, 300, 3) * 255
    image = Image.fromarray(rgb_array.astype('uint8')).convert('RGB')
    filename = image_id + '.jpg'
    image.save(out + filename)

    figure = E.figure(
                E.title(gen_heading_name()),
                E.mediaobject(
                    E.alt(gen_heading_name()),
                    E.imageobject(
                        E.imagedata(fileref=filename)
                    )
                ),
                id=image_id)
    paragraphs[para].addnext(figure)
    images.append(image_id)


# Adding Links to Images
for para in progressbar([random.randint(0, len(paragraphs)-1) for _ in range(MAXCNT_IMAGELINK)], prefix="Linking Images: "):
    pos = random.randint(0, len(paragraphs[para].text.split())-1)  # choose a random word of para for inserting link
    img = random.randint(0, len(images)-1)  # choose a random image as destination

    word = paragraphs[para].text.split()[pos]
    start_index = paragraphs[para].text.find(word)  # find the position index of the word inside the string

    if start_index is None:  # word not found inside the string
        continue  # skip

    end_index = start_index + len(word)  # end position (index) of the word inside the string

    para_head = paragraphs[para].text[:end_index] + ' '  # first part of the paragraph
    para_tail = paragraphs[para].text[end_index:]  # tail of the paragraph

    xref = etree.SubElement(paragraphs[para], "xref", linkend=images[img])
    paragraphs[para].append(xref)  # inserting link in the paragraph (will be placed at the end)

    paragraphs[para].text = para_head  # replacing the text of the paragraph (head)
    xref.tail = para_tail  # adding the tail after the link



# Pretty Print
# print(etree.tostring(document, pretty_print=True, method='xml', encoding=str))

# Save output
tree = etree.ElementTree(document)
tree.write(out + 'output.xml', pretty_print=True, xml_declaration=True,   encoding="utf-8")
