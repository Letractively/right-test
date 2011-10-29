#-*- coding: utf-8 -*-

# Copyright 2011 Lenshin Dmitry
# This file is part of RightTest.

# RightTest is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# RightTest is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with RightTest.  If not, see <http://www.gnu.org/licenses/>.

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import SocketServer
import test

from test import TestSet
from interface import AdminInterface, TestEditInterface, ResultsInterface, DummyInterface, \
			ScreenTestInterface, ListTestInterface, ControlTestInterface, TestXmlInterface, UsersXmlInterface, ReportInterface
import storage
from hashlib import md5
import random

import Cookie
import os
import cgi
import sys

import webbrowser
import threading
import time

from settings import PORT

from xml.sax.saxutils import escape, quoteattr


test.initTestSet()
storage.initStorage()

class Handler(BaseHTTPRequestHandler):

    usersData = {}

    #Global settings for test
    settings = {}
    
    interfaces = {}
    interfaces['admin'] = AdminInterface(interfaces)
    interfaces['edit'] = TestEditInterface()
    interfaces['results'] = ResultsInterface()
    interfaces['test'] = DummyInterface()
    interfaces['xmltest'] = TestXmlInterface()
    interfaces['xmlusers'] = UsersXmlInterface()
    interfaces['controltest'] = ControlTestInterface()
    interfaces['report'] = ReportInterface()

    testSet = TestSet()
    
    sessionUsers = []
    
    def parse_param(self):
	''' Parameters are in form http://url/param1/param2/... '''
        param = self.path.split('/')
        ret = []
        for p in param:
    	  if p.strip() != "": ret.append(p)

	if len(ret) == 0:
	    return ['']
	else:
	    return ret

    def is_private(self):
	return (self.client_address[0] == '127.0.0.1')

    def pic_page(self, param):
	'''Load images. All images must be in templates/media/ directory 
	   in page image must be refered as "/media/filename"
	'''
	
        self.send_response(200)
        ext  = os.path.splitext(param[1])[1][1:].lower()
        self.send_header("Content-type", "image/"+ext)
        self.end_headers()
        if param[1].rfind('/') == param[1].rfind('\\') == -1:
	    try:
                pic = open('templates/media/'+param[1], 'rb')
		self.wfile.write(pic.read())
		pic.close()
		self.wfile.close()
	    except:
		print >> sys.stderr, 'No such picture '+param[1]

    def generateSid(self):
	while True:
	    sid = md5(str(random.random())).hexdigest()
	    sid = sid[:6]
	    if not os.path.exists(storage.USER_PATH+sid):
		return sid

    def showInterface(self, form=None):
	param = self.parse_param()
	private = self.is_private()
	
	if param[0] == "":
	    page = 'admin' if private else 'test'
	else:
	    page = param[0]

	interface = self.interfaces.get(page)
	if interface:
	    if interface.private == True and not private:
		interface = DummyInterface()
	else:
	    interface = DummyInterface()

	interface.show(http_handler=self, param=param, form=form)

    def initSession(self):
	if not self.usersData.has_key( self._sessionSid() ):
	    sid = self.generateSid()
	    self.send_header("Set-Cookie", "sid=%s; path=/"%sid)
	    self.usersData[sid] = {}

    def _sessionSid(self):
	if self.headers.has_key('Cookie'):
	    cookie = Cookie.SimpleCookie(self.headers['Cookie'])
	    if cookie.has_key('sid'):
		return cookie['sid'].value
	    else:
		return None
	else:
	    return None

    def dropSession(self):
	sid = self._sessionSid()
	try:
	    self.usersData.pop(sid)
	except:
	    pass

    def session(self):
	sid = self._sessionSid()
	return self.usersData.get(sid)

    def sessionData(self, key):
	sid = self._sessionSid()
	if self.usersData.has_key(sid):
	    return self.usersData[sid].get(key)

	return None

    def sessionSetData(self, key, data):
	sid = self._sessionSid()
	if self.usersData.has_key(sid):
	    self.usersData[sid][key] = data

    def initStorage(self, user_name, user_rank, test):
	sid = self._sessionSid()
	stor = storage.Storage(sid, user_name, user_rank, test)
	self.sessionUsers.append(stor)
	self.sessionSetData('storage', stor)

    def setSettings(self, test_name, test_count, test_mode):
	self.settings['test_name']  = test_name
	self.settings['test_count'] = test_count
	self.settings['test_mode'] = test_mode

	if test_mode == 'list':
	    interface = ListTestInterface()
	else:
	    interface = ScreenTestInterface()
	
	self.interfaces['test'] = interface

    def activeUsersXmlList(self):
	ret = "<users>"
	sid = self._sessionSid()
	for stor in self.sessionUsers:
	    complete = 1 if stor.test.isComplete() else 0
	    ret += '<user name=%s result="%i" answered="%i" complete="%i" />'%(quoteattr(stor.user_name), stor.result, stor.answer.count(), complete)
	ret += "</users>"
	return ret

    def stopTesting(self):
	self.interfaces['test'] = DummyInterface()

	self.settings.clear()
	while(len(self.sessionUsers)):
	    self.sessionUsers.pop()
	self.usersData.clear()


    def testIsStart(self):
	if self.settings.has_key('test_name'):
	    return True
	return False

    def do_GET(self):
	param = self.parse_param()
	if param[0] == 'media' and len(param) == 2:
	    self.pic_page(param)
	else:
	    self.showInterface()

    def do_POST(self):
        form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD':'POST',
                             'CONTENT_TYPE':self.headers['Content-Type'],
                          })

	self.showInterface(form)



class WebBrowser(threading.Thread):
    def run(self):
	time.sleep(1)
	webbrowser.open("http://127.0.0.1:%i/"%PORT)


class MultiThreadedHTTPServer(SocketServer.ThreadingMixIn, HTTPServer):
    pass

if __name__ == '__main__':
    
    WebBrowser().start()
    
    server = MultiThreadedHTTPServer(('', PORT), Handler)
    server.serve_forever()