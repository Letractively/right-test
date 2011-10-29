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

import socket

from template import Template
from test import Test, Question
import storage

from settings import PORT


REDIRECT_CODE=302

#Get IP address of real interface
try:
    WWW_ADDRESS = "http://%s:%i"%(socket.gethostbyname(socket.gethostname()), PORT)
except:
    WWW_ADDRESS = 'Адрес не определен'

class Interface:
    """
    Base class for all interfaces
    """
    def __init__(self, private=False):
	self.private = private

    def show(self, http_handler, param, form=None):
	"""
	Send html presentation of interface to client.
	This method must be overided id derived class.
	"""
	pass

    def redirect(self, http_handler, location):
	http_handler.send_response(REDIRECT_CODE)
	http_handler.send_header("Location", location)
	http_handler.end_headers()

    def answer(self, http_handler, text, context_type="text/html"):
        ''' Send simple text answer to client '''
        http_handler.send_response(200)
        http_handler.initSession()
        http_handler.send_header("Content-type", context_type)
        http_handler.end_headers()
        http_handler.wfile.write(text.encode("utf-8"))
        http_handler.wfile.close()

class BaseTestInterface(Interface):
    """
    This is base interface for testting, only registration done heare
    """
    def __init__(self):
	Interface.__init__(self)

    def register(self, http_handler, param, form=None):
	test =  http_handler.testSet.getByTid( http_handler.settings.get('test_name') )
	if form:
	    try:
		user_name = form['user_name'].value.decode("utf-8")
		user_rank = form['user_rank'].value.decode("utf-8")
	    except:
		user_name = u""
		user_rank = u""
	    
	    if test and user_name and  user_rank:
		test = test.getRandomSubTest(http_handler.settings.get('test_count', 0))
		http_handler.initStorage(user_name, user_rank, test)

	    self.redirect(http_handler, "/test")
	else:
	    template = Template('base.html')
	    template.setTemplate('INFO_BLOCK', 'test_info.html')
	    template.setData('TEST_TITLE', test.caption)

	    template.setTemplate('CONTENT', 'register.html')
	    self.answer(http_handler, template.show())

class AdminInterface(Interface):
    """
    From this interfase administrator can start, configure and stop testing
    """
    def __init__(self, interfaces):
	self.interfaces = interfaces
	Interface.__init__(self, private=True)

    #def getTest(self, http_handler):

    def show(self, http_handler, param, form=None):
	if form and form.has_key('test_name') and form.has_key('test_count') and form.has_key('test_mode'):
	    http_handler.setSettings(form['test_name'].value, int(form['test_count'].value), form['test_mode'].value)
	elif len(param) == 2 and param[1] == 'stop':
	    http_handler.stopTesting()
	    self.redirect(http_handler, "/admin")

	template = Template('base.html')
	if http_handler.testIsStart():
	    template.setTemplate('CONTENT', 'admin_status.html')
	    test = http_handler.testSet.getByTid(http_handler.settings.get('test_name'))
	    if test:
		template.setData('CURR_TEST', test.caption)
		template.setData('QUESTIONS_COUNT', str(http_handler.settings.get('test_count')))
		modes = {'screen': u"экранами", 'list': u"списком"}
		template.setData('TEST_DISPLAY_MODE', modes.get( http_handler.settings.get('test_mode') ))
	else:
	    template.setTemplate('CONTENT', 'admin.html')
	    template.setData('TEST_LIST', http_handler.testSet.htmlSelectList())

	template.setTemplate('INFO_BLOCK', 'admin_menue.html')
	template.setData('WWW_ADDRESS', WWW_ADDRESS)

	self.answer(http_handler, template.show())


class UsersXmlInterface(Interface):
    """
    Represent active users as XML
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	self.answer(http_handler, http_handler.activeUsersXmlList(), context_type="text/xml")


class TestXmlInterface(Interface):
    """
    Represent test as XML
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	param_count = len(param)
	if param_count == 2:
	    test = http_handler.testSet.getByTid(param[1])
	    """
	    try:
		part = int(param[2])
	    except:
		part = 0
	    """
	    self.answer(http_handler, test.serializeToXml(), context_type="text/xml")

class TestEditInterface(Interface):
    """
    From this interface administrator can edit existing or add new tests
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	param_count = len(param)
	if param_count == 1:
	    if form:
		#Add new test
		test_name = form['new_test_name'].value.decode("utf-8")
		test = Test(test_name)
		tid = http_handler.testSet.addTest(test)

		self.redirect(http_handler, '/edit/'+tid)
	    else:
		#Show list of all available test
		template = Template('base.html')
		template.setTemplate('CONTENT', 'edit.html')
		template.setTemplate('INFO_BLOCK', 'admin_menue.html')
		template.setData('TEST_LIST', http_handler.testSet.htmlLinkList())

		self.answer(http_handler, template.show())

	elif param_count == 3 and param[1]=='del':
	    http_handler.testSet.delTest(param[2])
	    self.redirect(http_handler, '/edit/')

	elif param_count == 2:
	    if form:
		try:
		    qcount = int(form['qcount'].value)
		except:
		    qcount = 0

		#Save modifications for test
		test = Test(form['caption'].value.decode("utf-8"))

		for i in xrange(qcount):
		    if form.has_key('q%i'%i):
			try:
			    points = int(form['p%i'%i].value)
			except:
			    points = 1
			
			if form.has_key('h%i'%i):
			    qhint = form['h%i'%i].value.decode("utf-8")
			else:
			    qhint = ""
			
			question = Question(form['q%i'%i].value.decode("utf-8"), qhint, points)
			try:
			    acount = int(form['acount%i'%i].value)
			except:
			    acount = 0

			for a in xrange(acount):
			    akey = 'a%i_%i'%(i, a)
			    if form.has_key(akey):
				if form.has_key('r%i_%i'%(i, a)):
				    question.addRight(form[akey].value.decode("utf-8"))
				else:
				    question.addWrong(form[akey].value.decode("utf-8"))

			test.addQuestion(question)

		http_handler.testSet.replaceTest(test, param[1])
		self.answer(http_handler, '<ok/>', context_type="text/xml")
	    else:
		template = Template('base.html')
		template.setTemplate('CONTENT', 'edit_test_item.html')
		template.setTemplate('INFO_BLOCK', 'admin_menue.html')
		template.setData('TEST_NAME', param[1])
		self.answer(http_handler, template.show())


class ResultsInterface(Interface):
    """
    Dummy interface
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	template = Template('base.html')
	template.setTemplate('CONTENT', 'results.html')
	template.setTemplate('INFO_BLOCK', 'admin_menue.html')
	template.setData('USERS', storage.recordsHtmlInfo())

	self.answer(http_handler, template.show())


class ControlTestInterface(Interface):
    """
    Show already commissioned test
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	template = Template('base.html')
	template.setTemplate('CONTENT', 'control_test.html')
	template.setTemplate('INFO_BLOCK', 'admin_menue.html')
	template.setData('TEST', storage.userControlTestHtml(param[1]))

	report = storage.userReport(param[1])
	for key in report:
	    template.setData(key, report[key])

	self.answer(http_handler, template.show())

class ReportInterface(Interface):
    """
    Show report for user
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	template = Template('base.html')
	template.setTemplate('CONTENT', 'report.html')
	template.setTemplate('INFO_BLOCK', 'admin_menue.html')

	report = storage.userReport(param[1])
	for key in report:
	    template.setData(key, report[key])

	self.answer(http_handler, template.show())

class DummyInterface(Interface):
    """
    Dummy interface
    """
    def __init__(self):
	Interface.__init__(self, private=True)

    def show(self, http_handler, param, form=None):
	template = Template('base.html')
	template.setTemplate('CONTENT', 'wait.html')
	template.setTemplate('INFO_BLOCK', 'test_dummy.html')
	template.setData('META', '<meta http-equiv="Refresh" content="3; url=/test">')

	self.answer(http_handler, template.show())

class ScreenTestInterface(BaseTestInterface):
    """
    Show test in one question per screen mode
    """
    def __init__(self):
	BaseTestInterface.__init__(self)

    def nextQuestion(self, session, storage):
	cur_question =  session.get('curr_question', 0)+1
	if  cur_question < len(storage.test.questions):
	    question = storage.test.questions[cur_question]
	    session['curr_question'] = cur_question
	    return question
	else:
	    return None

    def currentQuestion(self, session, storage):
	cur_question = session.get('curr_question', 0)
	if  cur_question < len(storage.test.questions):
	    return storage.test.questions[cur_question]
	else:
	    return None

    def show(self, http_handler, param, form=None):
	storage = http_handler.sessionData('storage')

	if storage == None:
	    self.register(http_handler, param, form)
	else:
	    session = http_handler.session()
	
	    question = self.currentQuestion(session, storage)

	    hint_field = ""

	    if form != None and question:
		if not form.has_key('hint'):
		    storage.populateAnswers(form)
		    question.applyAnswers(storage.answer)
		    storage.saveResult()

		    if question.getPoints() != 0:
			question = self.nextQuestion(session, storage)
		    else:
			hint_field = '<input type="hidden" name="hint" value="1">'
		else:
		    question = self.nextQuestion(session, storage)

	    template = Template('base.html')
	    template.setTemplate('INFO_BLOCK', 'test_info.html')
	    template.setData('TEST_TITLE', storage.test.caption)
	    if question:
		template.setTemplate('CONTENT', 'test_screen.html')

		template.setData('CURRENT', u'%i'%(session.get('curr_question', 0)+1) )
		template.setData('TOTTAL', u'%i'%(len(storage.test.questions)) )

		template.setData('QUESTION', question.serializeForHtml()+hint_field)
		if hint_field:
		    template.setData('ERROR', u'Ошибка')
		    template.setData('NEXT', u'Далее')
		else:
		    template.setData('NEXT', u'Ответить')
	    else:
		storage.test.setComplete()
		template.setTemplate('CONTENT', 'test_screen_end.html')
		template.setData('RESULT', str(storage.test.getPoints()))
		http_handler.dropSession()

	    self.answer(http_handler, template.show())

class ListTestInterface(BaseTestInterface):
    """
    Show test with all questions at once
    """
    def __init__(self):
	BaseTestInterface.__init__(self)

    def show(self, http_handler, param, form=None):
	storage = http_handler.sessionData('storage')
	if storage == None:
	    self.register(http_handler, param, form)
	else:
	    template = Template('base.html')
	    template.setTemplate('INFO_BLOCK', 'test_info.html')
	    template.setData('TEST_TITLE', storage.test.caption)

	    if form != None:
		storage.populateAnswers(form)
		storage.test.applyAnswers(storage.answer)
		storage.test.setComplete()
		storage.saveResult()
	        template.setTemplate('CONTENT', 'test_list_end.html')
		template.setData('RESULT', u"%i"%storage.test.getPoints())
		http_handler.dropSession()
	    else:
	        template.setTemplate('CONTENT', 'test_list.html')

	    template.setData('TEST', storage.test.serializeForHtml(show_hint=False))
	    self.answer(http_handler, template.show())

