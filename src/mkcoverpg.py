import Image, ImageDraw, ImageFont, os

from Watermark import watermark
import StringIO

def CreateBlank():
	img = Image.new("RGB", (527, 700), "white")
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
		font = ImageFont.truetype(os.environ['WINDIR'] + "/Fonts/" + fontname, size)
	
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
	
	img = drawCenterText(img, 10, title, "verdana.TTF", 36)
	img = drawCenterText(img, 48, author, "verdana.TTF", 24)
	#img = drawCenterText(img, img.size[1] - 50, logo_text, "COUR.TTF", 14)
	
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