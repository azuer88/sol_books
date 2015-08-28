#!/usr/bin/env python

from PIL import  Image
from PIL import ImageDraw
from PIL import ImageFont
import os

from Watermark import watermark
import StringIO
import logging

from fileutils import get_base_parent_path

BASE_DIR = get_base_parent_path()
FONT_VERDANA = os.path.join(BASE_DIR, 'fonts', 'verdana.ttf')
FONT_COURIER = os.path.join(BASE_DIR, 'fonts', 'cour.ttf')

def CreateBlank():
    img = Image.new("RGB", (600, 800), "white")
    return img

def AddWatermark(img, mark, offset=0):
    iw, ih = img.size
    mw, mh = mark.size

    icw = iw / 2
    ich = ih / 2

    xm = icw - (mw / 2)
    ym = ih - mh - (offset + 50)

    return watermark(img, mark, (xm, ym))

def drawCenterText(img, y, text, fontname, size):

    w, h = img.size
    drw = ImageDraw.Draw(img)
    while True:
        #font = ImageFont.truetype(os.environ['WINDIR'] + "/Fonts/" + fontname, size)
        base = os.path.dirname(os.path.abspath(__file__))
        fname = os.path.join(base, fontname)
        logging.debug("loading font - %s" % fname)
        font = ImageFont.truetype(fname, size)

        tw, th = drw.textsize(text, font=font)

        if (tw < w):
            break
        size = size - 1

    x = (w - tw) / 2

    #print "drawing text (w=%d,h=%d,s=%d) at (%d, %d)" % (tw, th, size, x, y)
    drw.text((x, y), text, fill="black", font=font)

    #drw.line((0, 0) + img.size, fill=128)
    #drw.line((0, img.size[1], img.size[0], 0), fill=128)

    del drw

    return img


def MakeCoverPage(title, author, logo_text, logo_fname):

    img = CreateBlank()
    #print "Opening logo_fname = " + logo_fname
    mark = Image.open(logo_fname)

    img = drawCenterText(img, 10, title, FONT_VERDANA, 36)
    img = drawCenterText(img, 48, author, FONT_VERDANA, 24)
    img = drawCenterText(img, img.size[1] - 50, logo_text, FONT_COURIER, 14)

    img = AddWatermark(img, mark, 50)

    return img

def MakeCoverPageStr(title, author, logo_text, logo_fname):
    img = MakeCoverPage(title, author, logo_text, logo_fname)
    output = StringIO.StringIO()
    img.save(output, format="JPEG")
    content = output.getvalue()
    output.close()

    return content

def test():
    img = MakeCoverPage("title of the Book", "the author", "storiesonline.net", "SOL-Mini-Logo.jpg")
    img.show()


if __name__ == '__main__':
    test()
