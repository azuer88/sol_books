#!/usr/bin/env python
#
#
import glob
import cgi, os, SocketServer, sys, time, urllib
from SimpleHTTPServer import SimpleHTTPRequestHandler
from StringIO import StringIO
from operator import itemgetter
import socket
import qrcode

server_ip = "0.0.0.0"

def get_date_name(record):
    #return time.strftime("%Y%m%d%H%M%S", record[2])
	return time.strftime("%Y%m%d", record[2]) + record[0].lower()

class DirectoryHandler(SimpleHTTPRequestHandler):
    def list_directory(self, path):
        try:
            #list = os.listdir(path)
			list = glob.glob('*.epub')
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        #list.sort(key=lambda a: a.lower())
        f = StringIO()
        displaypath = cgi.escape(urllib.unquote(self.path))

        newlist = []
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            date_modified = os.path.getmtime(fullname) # orig: time.ctime(os.path.getmtime(fullname))
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            newlist.append((displayname, linkname, date_modified))

        f.write('<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">')
        f.write("<html>\n<title>%s epub listing</title>\n" % server_ip)
        f.write("<body>\n<h2>epub listing for %s</h2>\n" % server_ip)
        f.write("<hr>\n<ul>\n")
        for displayname, linkname, date_modified in sorted(newlist, key=itemgetter(2), reverse=True): # sort by date_modified, descending
            f.write('<li><a href="%s">%s</a>\n'
                    % (urllib.quote(linkname), cgi.escape(displayname)))
        f.write("</ul>\n<hr>\n</body>\n</html>\n")
        length = f.tell()
        f.seek(0)
        self.send_response(200)
        encoding = sys.getfilesystemencoding()
        self.send_header("Content-type", "text/html; charset=%s" % encoding)
        self.send_header("Content-Length", str(length))
        self.end_headers()
        return f

def getLocalIP():
  s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  s.connect(('192.168.1.1', 0)) # connect to router (assumed at 192.168.1.1)
  return s.getsockname()[0]

def main():
  import argparse

  global server_ip

  port = 8000
  rootpath = os.getcwd()

  parser = argparse.ArgumentParser(description="Serve EPub books through HTTP")
  parser.add_argument("path",
     nargs='?',
     default=rootpath,
     help='location of EPub books to serve from, no subfolders will be shown, defaults to current directory',
     )
  parser.add_argument("-p", "--port", type=int,
     default=port, required=False,
     help='port of the HTTP server, defaults to 8000',
     )
  parser.add_argument("-a", "--address", type=str,
     default='', required=False,
     help='ip address of the HTTP server',
     )
  parser.add_argument("--show-qr", dest="show_qr",
     action='store_true')
  parser.add_argument("--no-show-qr", dest="show_qr",
     action='store_false')
  parser.set_defaults(show_qr=True)

  args = parser.parse_args()

  argspath = os.path.abspath(args.path)

  if (argspath!=rootpath):
    os.chdir(argspath)
  if (args.address):
    server_ip = args.address
  else:
    server_ip = getLocalIP()

  httpd = SocketServer.TCPServer((server_ip, args.port), DirectoryHandler)
  #server_ip = getLocalIP()

  #httpd = SocketServer.TCPServer(("", port), DirectoryHandler)
  print "serving at %s:%d" % (server_ip, args.port)
  print "root at ", argspath
  url = "http://%s:%d" % (server_ip, args.port)
  img = qrcode.make(url)
  img.show()
  httpd.serve_forever()

  return 0

if __name__ == "__main__":
	import sys
	sys.exit(main())
