from lxml import etree as ET
import lxml.builder as builder
from lxml import html as HT
from lxml.etree import Element 
import os
import zipfile

import htmlentitydefs, re

import logging
 
def slugify(text, separator="-"):
  ret = ""
  for c in text.lower():
    try:
      ret += htmlentitydefs.codepoint2name[ord(c)]
    except:
      ret += c
 
  ret = re.sub("([a-zA-Z])(uml|acute|grave|circ|tilde|cedil)", r"\1", ret)
  ret = re.sub("\W", " ", ret)
  ret = re.sub(" +", separator, ret)
 
  return ret.strip()
		
class ContainerXML(object):
	"""
	handles the creation of the 'container.xml' 
	"""
	def __init__(self):
		self.encoding = 'utf-8'
		self.ns = "urn:oasis:names:tc:opendocument:xmlns:container"
		self.version = "1.0"
		self.media_type = "application/oebps-package+xml"
		self.full_path = "OEBPS/content.opf"
	def build(self):
		root = ET.Element("container", xmlns=self.ns, version=self.version)
		rfs = ET.SubElement(root, "rootfiles")
		attrs = {"full-path": self.full_path, "media-type": self.media_type, }
		rf = ET.SubElement(rfs, "rootfile", **attrs)
		return root 
		
	def __repr__(self):
		root = self.build()
		return ET.tostring(root, pretty_print=True, xml_declaration=True, encoding=self.encoding)
		
class ContainerOPF(object):
	"""
	Handles the creation of content.opf
		it has attribues 'manifest' and 'spines' which are lists of tuples
		to add items, use 'addManifest' and addSpine', respectively.
	"""
	def __init__(self):
		self.encoding = "utf-8"
		self.ns_opf = "http://www.idpf.org/2007/opf"
		self.ns_dc = "http://purl.org/dc/elements/1.1/"
		self.NSMAP = {
			None : self.ns_opf,
			"dc" : self.ns_dc,
			}
		self.ATTR = {
			"xmlns": self.ns_opf,
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
		root = ET.Element("package", **self.ATTR)
		self.buildMeta(root)
		self.buildManifest(root)
		self.buildSpine(root)
		return root
		
	def addManifest(self, id, src, media_type):
		t = (id, src, media_type)
		self.manifest.append(t)
		
	def addSpine(self, id, linear):
		t = (id, linear)
		self.spine.append(t)
		
	def buildMeta(self, root):
		ns = {"dc": self.ns_dc, }
		metadata = ET.SubElement(root, "metadata", nsmap=ns)
		ET.SubElement(metadata, '{%s}title' % self.ns_dc).text = self.title
		ET.SubElement(metadata, '{%s}creator' % self.ns_dc).text = self.author
		ET.SubElement(metadata, '{%s}identifier' % self.ns_dc, id='bookid').text ="urn:uuid:%s" % self.bookid
		ET.SubElement(metadata, '{%s}language' % self.ns_dc).text = self.language
		ET.SubElement(metadata, 'meta', name="cover", content="cover-image")

	def buildManifest(self, root):
		m = ET.SubElement(root, "manifest")
		for id, href, media_type in self.manifest:
			args = {"id": id, "href": href, "media-type": media_type}
			ET.SubElement(m, "item", **args)
	
	def buildSpine(self, root):
		s = ET.SubElement(root, "spine", toc="ncx")
		for idref, linear in self.spine:
			args = {"idref": idref, "linear": linear}
			ET.SubElement(s, "itemref", **args)
		
	def _test(self):
		self.manifest.append(('ncx', 'toc.ncx', 'application/x-dtbncx+xml'))
		self.manifest.append(('cover', 'title.html', 'application/xhtml+xml'))
		self.manifest.append(('cover-image', 'images/cover.jpg', 'image/jpg'))
		self.manifest.append(('css', 'stylesheet.css', 'text/css'))
		
		self.spine.append(('cover', 'no'))
		self.spine.append(('content', 'yes'))
		
		return self.build()
		
	def __repr__(self):
		root = self.build()
		return ET.tostring(root, xml_declaration=True, pretty_print=True, encoding=self.encoding)
		
class XHTMLFile(object):
	"""
	simplifies creation of xhtml files.
	"""
	def __init__(self):
		self.doctype="""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.1//EN"
    "http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd">"""
		self.xmlns = "http://www.w3.org/1999/xhtml"
		self.content = "Hello <b>world!</b><br/>this is another line<br/>"
		self.headers = []
		self.encoding = "utf-8"
		self.media_type = "application/xhtml+xml" 
		self.id = "chapter_id"
		self.part = None
		self.title = "chapter_title"

	@property
	def uid(self):
		if self.part:
			return "%s_%s" % (self.id, self.part)
		else:
			return self.id
			
	@property
	def filename(self):
		return "%s.xhtml" % self.uid
		
	def build(self):
		root = ET.Element("html", xmlns=self.xmlns)
		self.buildHead(root)
		self.buildBody(root)
		return root
		
	def buildHead(self, root):
		head = ET.SubElement(root, "head")
		for k, v, a in self.headers:
			if v:
				ET.SubElement(head, k, **a).text = v
			else:
				ET.SubElement(head, k, **a)
		ET.SubElement(head, "title").text = self.title
		
	def buildBody(self, root):
		fragments = HT.fragments_fromstring(self.content)
		body = ET.SubElement(root, "body")
		last = None
		for frag in fragments:
			if isinstance(frag, ET._Element):
				body.append(frag)
				last = frag
			else:
				if last:
					last.tail = fag
				else: 
					body.text = frag
		
	def _test(self):
		self.headers.append(("title", "test title", {}))
		self.headers.append(("link", "", {"href": "../Styles/style.css", "rel": "stylesheet", "type": "text/css"}))
		
		return self.build()
		
	def __repr__(self):
		root = self.build()
		return ET.tostring(root, xml_declaration=True, pretty_print=True, encoding=self.encoding, doctype=self.doctype)
		
	def save(self, target_dir):
		filename = target_dir + os.path.sep + self.filename
		
		f = open(filename, "w+t")
		f.write(self.__repr__())
		f.close()
		
class TOCNCX(object):
	"""
	Handles the creation of toc.ncx
	"""
	def __init__(self):
		self.doctype = """<!DOCTYPE ncx PUBLIC "-//NISO//DTD ncx 2005-1//EN"
                 "http://www.daisy.org/z3986/2005/ncx-2005-1.dtd">"""
		self.encoding = "utf-8"
		self.ns = "http://www.daisy.org/z3986/2005/ncx/"
		self.version = "2005-1"
		self.bookid = "bookid"
		self.title = "title"
		self.items = []
		
	def build(self):
		root = ET.Element("ncx", xmlns=self.ns, version=self.version)
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
		docTitle = ET.SubElement(root, "docTitle")
		ET.SubElement(docTitle, "text").text = self.title
		navMap = ET.SubElement(root, "navMap")
		seq = 1
		for id, label, src in self.items:
			navPt = ET.SubElement(navMap, "navPoint", id=id, playOrder=str(seq))
			navLbl = ET.SubElement(navPt, "navLabel")
			ET.SubElement(navLbl, "text").text = label
			ET.SubElement(navPt, "content", src=src)
			seq += 1 
		return root
		
	def addItem(self, id, title, src):
		t = (id, title, src)
		self.items.append(t)
		
	def _test(self):
		self.items.append(("navpoint-1", "Book Cover", "title.html"))
		self.items.append(("navpoint-2", "Contents", "content.html"))
		
		return self.build()
		
	def __repr__(self):
		root = self.build()
		return ET.tostring(root, xml_declaration=True, pretty_print=True, encoding=self.encoding, doctype=self.doctype)
		
class EPub(object):
	"""
	Handles the creation of the actual epub file.
		addition of cover image must be done first, since order of adding chapter is significant
	"""
	TEXT = 'Text'
	IMAGES = 'Images'
	STYLES = 'Styles'
	def __init__(self, title, author, bookid, folder=""):
		self.opf = ContainerOPF()
		self.xml = ContainerXML()
		self.ncx = TOCNCX()
		self.oebps = ""

		if folder:
			self.folder = folder
		else:
			self.folder = os.path.join(os.getcwd(), str(bookid))
			
		self.setBookId(bookid)
		self.setTitle(title)
		self.setAuthor(author)
				
		self.zip = zipfile.ZipFile(self.filename, "w", zipfile.ZIP_DEFLATED)
		
		# write mimetype
		self.zip.writestr("mimetype", "application/epub+zip", zipfile.ZIP_STORED)
		
		# add toc.ncx to content.opf
		self.opf.addManifest("ncx", "toc.ncx", "application/x-dtbncx+xml")
		
	@property 
	def filename(self):
		return "%s by %s.epub" % (self.title, self.author)
		
	def close(self):
		# write META-INF
		self.zip.writestr("META-INF/container.xml", str(self.xml))
		# write content.opf
		self.zip.writestr("OEBPS/content.opf", str(self.opf))
		# write toc.ncx
		self.zip.writestr("OEBPS/toc.ncx", str(self.ncx))
		self.zip.close()
				
	def setBookId(self, bookid):
		self.bookid = str(bookid)
		self.opf.bookid = str(bookid)
		self.ncx.bookid = str(bookid)
		
	def setTitle(self, title):
		self.title = title
		self.opf.title = title
		self.ncx.title = title
		
	def setAuthor(self, author):
		self.author = author
		self.opf.author = author
		
	def addChapter(self, xhtml, linear="yes"):
		assert isinstance(xhtml, XHTMLFile)
		
		src = "%s/%s" % (self.TEXT, xhtml.filename)
		self.opf.addManifest(xhtml.uid, src, xhtml.media_type)
		self.opf.addSpine(xhtml.uid, linear)
		
		self.ncx.addItem(xhtml.uid, xhtml.title, src)
		
		filename = os.path.join("OEBPS", self.TEXT, xhtml.filename)		
		self.zip.writestr(filename, str(xhtml))
		
	def addCoverImage(self, image_str):
		import shutil
		assert len(self.opf.spine)==0 
		
		src = "%s/%s" % (self.IMAGES, "cover.jpg")
		filename = os.path.join("OEBPS", self.IMAGES, "cover.jpg")
		self.zip.writestr(filename, image_str)
		
		self.opf.addManifest("cover-image", src, "image/jpeg")
		x = XHTMLFile()
		x.id = "cover"
		x.title = "Cover Page"
		x.content = "<p><img alt=\"%s\" src=\"../%s\" /></p>" % (self.title, src)
		x.headers.append(("style", "img { max-width: 100%; }", {"type":"text/css",}))
		self.addChapter(x, "no")
		
	def addStyle(self, str, content=""):
		if content:
			src = self.addStyleStr(content, str) # str is name of css file to use
		else:
			src = self.addStyleFile(str) # str is filename of actual css file
		self.opf.addManifest(slugify(src), src, "text/css")
		
	def addStyleStr(self, style_str, fname="stylesheet.css"):
		filename = os.path.join("OEBPS", self.STYLES, fname)
		self.zip.writestr(filename, style_str)
		return "%s/%s" % (self.STYLES, fname)
		
	def addStyleFile(self, style_filename):
		name = os.path.basename(style_filename)
		filename = os.path.join("OEBPS", self.STYLES, name)
		self.zip.write(style_filename, filename)
		return "%s/%s" % (self.STYLES, name)
		
def test_main():
	from mkcoverpg import MakeCoverPageStr
	#from SOLBook import SOLStory
	#s = SOLStory(56030)
	e = EPub("test epub", "author", "test")
	x = XHTMLFile()
	x.id = "chapter_01"
	x.title = "Chapter 1"
	x.content = "this is the content of <b>chapter 1</b>"
	x.headers.append(("link", None, {"rel": "styleshee", "type": "text/css", "href": "../Styles/style.css"}))
	img = MakeCoverPageStr("title of the Book", "the author", "storiesonline.net", "SOL-Mini-Logo.jpg")
	e.addCoverImage(img)
	e.addStyle("bin/data/style.css")
	e.addChapter(x)
	e.close()
	
	
if __name__ == "__main__":
	import sys
	sys.exit(test_main())
