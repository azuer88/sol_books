#!/usr/bin/env python
"""
epub object to create an epub ebook
"""
from lxml import etree as ET
#import lxml.builder as builder
from lxml import html as HT
#from lxml.etree import Element
import os
import zipfile

import htmlentitydefs, re

#import logging

def valid_filename(strname):
    """
    create a valid filename from given a string
    """
    import string
    import os

    fname_only, fext_only = os.path.splitext(strname)
    valid_chars = "-_() %s%s" % (string.ascii_letters, string.digits)
    #valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    valid_fname = ''.join(c for c in fname_only if c in valid_chars)
    return valid_fname + fext_only

def sluggify(text, separator="-"):
    """
    sluggify text
    """
    ret = ""
    for char in text.lower():
        try:
            ret += htmlentitydefs.codepoint2name[ord(char)]
        except: # pylint: disable-msg=W0702
            ret += char

    ret = re.sub(r"([a-zA-Z])(uml|acute|grave|circ|tilde|cedil)", r"\1", ret)
    ret = re.sub(r"\W", r" ", ret)
    ret = re.sub(r" +", separator, ret)
    ret = re.sub(r":", r">", ret)
    return ret.strip()

class ContainerXML(object):
    """
    encapsulate the XML Container structure
    """
    def __init__(self):
        self.encoding = 'utf-8'
        self.namespace = "urn:oasis:names:tc:opendocument:xmlns:container"
        self.version = "1.0"
        self.media_type = "application/oebps-package+xml"
        self.full_path = "OEBPS/content.opf"
    def build(self):
        """
        build an XML container structure
        """
        root = ET.Element("container", xmlns=self.namespace,
                          version=self.version)
        rfs = ET.SubElement(root, "rootfiles")
        attrs = {"full-path": self.full_path, "media-type": self.media_type, }
        dummy = ET.SubElement(rfs, # pylint: disable-msg=W0142
                              "rootfile", **attrs)
        return root
    def dummy(self):
        """
        dummy method
        """
        pass
    def __repr__(self):
        root = self.build()
        return ET.tostring(root, pretty_print=True, xml_declaration=True,
                           encoding=self.encoding)

class ContainerOPF(object): # pylint: disable=too-many-instance-attributes
    """
    encapsulte OPF Container structure
    """
    def __init__(self):
        self.encoding = "utf-8"
        self.namespace_opf = "http://www.idpf.org/2007/opf"
        self.namespace_dc = "http://purl.org/dc/elements/1.1/"
        self.namespace_map = {
            None : self.namespace_opf,
            "dc" : self.namespace_dc,
            }
        self.attr = {
            "xmlns": self.namespace_opf,
            "unique-identifier": "bookid",
            "version": "2.0",
            }

        self.title = "sample"
        self.author = "me"
        self.language = "en"
        self.bookid = "bookid"

        self.manifest = []
        self.spine = []

    def build(self):
        """
        build the OPF Container structure
        """
        root = ET.Element("package", **self.attr)
        self.build_meta(root)
        self.build_manifest(root)
        self.build_spine(root)
        return root

    def add_manifest(self, sid, src, media_type):
        """
        add manifest to the OPF Container structure
        """
        tmp = (sid, src, media_type)
        self.manifest.append(tmp)

    def add_spine(self, sid, linear):
        """
        add spine to the OPF Container structure
        """
        tmp = (sid, linear)
        self.spine.append(tmp)

    def build_meta(self, root):
        """
        build the meta of the OPF Container structure
        """
        ns_dc = {"dc": self.namespace_dc, }
        metadata = ET.SubElement(root, "metadata", nsmap=ns_dc)
        ET.SubElement(metadata,
                      '{%s}title' % self.namespace_dc).text = self.title
        ET.SubElement(metadata,
                      '{%s}creator' % self.namespace_dc).text = self.author
        ET.SubElement(metadata,
                      '{%s}identifier' % self.namespace_dc,
                      id='bookid').text = "urn:uuid:%s" % self.bookid
        ET.SubElement(metadata,
                      '{%s}language' % self.namespace_dc).text = self.language
        ET.SubElement(metadata, 'meta', name="cover", content="cover-image")

    def build_manifest(self, root):
        """
        build the manifest of the OPF Container structure
        """
        manifest = ET.SubElement(root, "manifest")
        for sid, href, media_type in self.manifest:
            args = {"id": sid, "href": href, "media-type": media_type}
            ET.SubElement(manifest, "item", **args) # pylint: disable-msg=W0142

    def build_spine(self, root):
        """
        build the spine of the OPF Container structure
        """
        spine = ET.SubElement(root, "spine", toc="ncx")
        for idref, linear in self.spine:
            args = {"idref": idref, "linear": linear}
            ET.SubElement(spine, "itemref", **args) # pylint: disable-msg=W0142

    def _test(self):
        """
        test method
        """
        self.manifest.append(('ncx', 'toc.ncx', 'application/x-dtbncx+xml'))
        self.manifest.append(('cover', 'title.html', 'application/xhtml+xml'))
        self.manifest.append(('cover-image', 'images/cover.jpg', 'image/jpg'))
        self.manifest.append(('css', 'stylesheet.css', 'text/css'))

        self.spine.append(('cover', 'no'))
        self.spine.append(('content', 'yes'))

        return self.build()

    def __repr__(self):
        root = self.build()
        return ET.tostring(root, xml_declaration=True,
                           pretty_print=True, encoding=self.encoding)

class XHTMLFile(object): # pylint: disable=too-many-instance-attributes
    """
    encapsulate an XTMLFile, eases the creation of a suitable xhtml file for
    epub consumption
    """
    def __init__(self):
        self.doctype = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""
        self.xmlns = "http://www.w3.org/1999/xhtml"
        self.content = "Hello <b>world!</b><br/>this is another line<br/>"
        self.headers = []
        self.encoding = "utf-8"
        self.media_type = "application/xhtml+xml"
        self.c_id = "chapter_id"
        self.part = None
        self.title = "chapter_title"

    @property
    def uid(self):
        """
        unique id of the XHTMLFile
        """
        if self.part:
            return "%s_%s" % (self.c_id, self.part)
        else:
            return self.c_id

    @property
    def filename(self):
        """
        property filename
        """
        return "%s.xhtml" % self.uid

    def build(self):
        """
        build and return an xhtml file
        """
        root = ET.Element("html", xmlns=self.xmlns)
        self.build_head(root)
        self.build_body(root)
        return root

    def build_head(self, root):
        """
        build the header from the fragments in root
        """
        head = ET.SubElement(root, "head")
        for key, val, attr in self.headers:
            if val:
                ET.SubElement(head, # pylint: disable-msg=W0142
                              key, **attr).text = val
            else:
                ET.SubElement(head, key, **attr) # pylint: disable-msg=W0142
        ET.SubElement(head, "title").text = self.title

    def build_body(self, root):
        """
        build the body of the xhtml file from the fragments in root
        """
        fragments = HT.fragments_fromstring(self.content)
        body = ET.SubElement(root, "body")
        last = None
        for frag in fragments:
            if isinstance(frag, ET._Element): # pylint: disable-msg=W0212
                body.append(frag)
                last = frag
            else:
                if last:
                    last.tail = frag
                else:
                    body.text = frag

    def _test(self):
        """
        test method
        """
        self.headers.append(("title", "test title", {}))
        self.headers.append(("link", "", {"href": "../Styles/style.css",
                            "rel": "stylesheet", "type": "text/css"}))

        return self.build()

    def __repr__(self):
        root = self.build()
        return ET.tostring(root, xml_declaration=True, pretty_print=True,
                           encoding=self.encoding, doctype=self.doctype)

    def save(self, target_dir):
        """
        save the xhtml file
        """
        filename = target_dir + os.path.sep + self.filename

        with open(filename, "w") as output:
            output.write(self.__repr__())

class TOCNCX(object):
    """
    oject to encapsulate a TOC/NCX structure
    """
    def __init__(self):
        self.doctype = """<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
                 "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">"""
        self.encoding = "utf-8"
        self.namespace = "http://www.daisy.org/z3986/2005/ncx/"
        self.version = "2005-1"
        self.bookid = "bookid"
        self.title = "title"
        self.items = []

    def build(self):
        """
        return an TOC/NCX structure object
        """
        root = ET.Element("ncx", xmlns=self.namespace, version=self.version)
        head = ET.SubElement(root, "head")
        ET.SubElement(head, "meta",
            content="urn:uuid:%s" % self.bookid,
            name="dtb:uid",
            )
        ET.SubElement(head, "meta",
            content="1",
            name="dtb:depth",
            )
        ET.SubElement(head, "meta",
            content="0",
            name="dtb:totalPageCount",
            )
        ET.SubElement(head, "meta",
            content="0",
            name="dtb:maxPageNumber",
            )
        doctitle = ET.SubElement(root, "docTitle")
        ET.SubElement(doctitle, "text").text = self.title
        navmap = ET.SubElement(root, "navMap")
        seq = 1
        for sid, label, src in self.items:
            navpt = ET.SubElement(navmap, "navPoint", id=sid,
                                  playOrder=str(seq))
            navlabel = ET.SubElement(navpt, "navLabel")
            ET.SubElement(navlabel, "text").text = label
            ET.SubElement(navpt, "content", src=src)
            seq += 1
        return root

    def add_item(self, sid, title, src):
        """
        add an item to the ncx structure
        """
        item = (sid, title, src)
        self.items.append(item)

    def _test(self):
        """
        debugging _test method
        """
        self.items.append(("navpoint-1", "Book Cover", "title.html"))
        self.items.append(("navpoint-2", "Contents", "content.html"))

        return self.build()

    def __repr__(self):
        root = self.build()
        return ET.tostring(root, xml_declaration=True, pretty_print=True,
                           encoding=self.encoding, doctype=self.doctype)

class EPub(object): # pylint: disable=too-many-instance-attributes
    """
    class to create epub ebook
    """
    #OEBPS = 'OEBPS'
    TEXT = 'Text'
    IMAGES = 'Images'
    STYLES = 'Styles'
    def __init__(self, title, author, bookid, folder="", prefix=""):
        self.opf = ContainerOPF()
        self.xml = ContainerXML()
        self.ncx = TOCNCX()
        self.oebps = ""
        self.author = ""
        self.title = ""
        self.bookid = 0
        self.prefix = prefix

        if folder:
            self.folder = folder
        else:
            self.folder = os.path.join(os.getcwd(), str(bookid))

        self.set_book_id(bookid)
        self.set_title(title)
        self.set_author(author)

        self.zip = zipfile.ZipFile(self.filename, "w", zipfile.ZIP_DEFLATED)

        # write mimetype
        self.zip.writestr("mimetype", "application/epub+zip",
                          zipfile.ZIP_STORED)

        # add toc.ncx to content.opf
        self.opf.add_manifest("ncx", "toc.ncx", "application/x-dtbncx+xml")

    @property
    def filename(self):
        """
        property filename of the ebook
        """
        return valid_filename("%s%s by %s.epub" % (self.prefix, self.title, self.author))

    def close(self):
        """
        close the ebook object and write out all pertinent data
        """
        # write META-INF
        self.zip.writestr("META-INF/container.xml", str(self.xml))
        # write content.opf
        self.zip.writestr("OEBPS/content.opf", str(self.opf))
        # write toc.ncx
        self.zip.writestr("OEBPS/toc.ncx", str(self.ncx))
        self.zip.close()

    def set_book_id(self, bookid):
        """
        set the book id, update opf and ncx
        """
        self.bookid = str(bookid)
        self.opf.bookid = str(bookid)
        self.ncx.bookid = str(bookid)

    def set_title(self, title):
        """
        set the title, updating opf and ncx
        """
        self.title = title
        self.opf.title = title
        self.ncx.title = title

    def set_author(self, author):
        """
        set the author, and set it in opf object too
        """
        self.author = author
        self.opf.author = author

    def add_chapter(self, xhtml, linear="yes"):
        """
        add a chapter, passing an XHTMLFile object
        """
        assert isinstance(xhtml, XHTMLFile)

        src = "%s/%s" % (self.TEXT, xhtml.filename)
        self.opf.add_manifest(xhtml.uid, src, xhtml.media_type)
        self.opf.add_spine(xhtml.uid, linear)

        self.ncx.add_item(xhtml.uid, xhtml.title, src)

        filename = os.path.join("OEBPS", self.TEXT, xhtml.filename)
        self.zip.writestr(filename, str(xhtml))

    def add_image(self, fname, image_str, sid=None):
        """
        add an image into the epub, from image_str as file named fname
        """
        src = "%s/%s" % (self.IMAGES, fname)
        if sid is None:
            sid = sluggify(src)
        self.opf.add_manifest(sid, src, "image/jpeg")
        filename = os.path.join("OEBPS", self.IMAGES, fname)
        self.zip.writestr(filename, image_str)

        return "../%s" % src

    def add_cover_image(self, image_str):
        """
        store image_str as the cover page image
        """
        #import shutil
        assert len(self.opf.spine) == 0

        #src = "%s/%s" % (self.IMAGES, "cover.jpg")
        #filename = os.path.join("OEBPS", self.IMAGES, "cover.jpg")
        #self.zip.writestr(filename, image_str)

        src = self.add_image("cover.jpg", image_str, "cover-image")

        # self.opf.add_manifest("cover-image", src, "image/jpeg")

        xfile = XHTMLFile()
        xfile.c_id = "cover"
        xfile.title = "Cover Page"
        xfile.content = "<p><img alt=\"%s\" src=\"%s\" /></p>" % \
                (self.title, src)
        xfile.headers.append(("style", "img { max-width: 100%; }",
                              {"type":"text/css",}))
        self.add_chapter(xfile, "no")

    def add_style(self, strstyle, content=""):
        """
        add a style to ebook, calling the correct help to add a file or string
        """
        if content: # str is name of css file to use
            src = self.add_style_str(content, strstyle)
        else: # str is filename of actual css file
            src = self.add_style_file(strstyle)

        self.opf.add_manifest(sluggify(src), src, "text/css")

    def add_style_str(self, style_str, fname="stylesheet.css"):
        """
        add a style string to ebook
        """
        filename = os.path.join("OEBPS", self.STYLES, fname)
        self.zip.writestr(filename, style_str)
        return "%s/%s" % (self.STYLES, fname)

    def add_style_file(self, style_filename):
        """
        add a style file to ebook
        """
        name = os.path.basename(style_filename)
        filename = os.path.join("OEBPS", self.STYLES, name)
        self.zip.write(style_filename, filename)
        return "%s/%s" % (self.STYLES, name)

def test_main():
    """
    test unit main()
    """
    from mkcoverpg import MakeCoverPageStr
    #from SOLBook import SOLStory
    #s = SOLStory(56030)
    with open('dnstairs.jpg', 'r') as inp:
        img = inp.read()
    ebook = EPub("test epub", "author", "test")
    src = ebook.add_image('dnstairs.jpg', img)
    xfile = XHTMLFile()
    xfile.c_id = "chapter_01"
    xfile.title = "Chapter 1"
    xfile.content = """
    this is the content of <b>chapter 1</b>
    <img alt="downstairs" title="downstairs" src="%s">
    """ % src
    xfile.headers.append(("link", None, {"rel": "styleshee",
                                         "type": "text/css",
                                         "href": "../Styles/style.css"}))
    img = MakeCoverPageStr("title of the Book",
                           "the author",
                           "storiesonline.net",
                           "data/SOL-Mini-Logo.jpg")
    ebook.add_cover_image(img)
    ebook.add_style("data/style.css")
    ebook.add_chapter(xfile)
    ebook.close()


if __name__ == "__main__":
    import sys
    sys.exit(test_main())

