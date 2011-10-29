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


import random
import os
import codecs
import math

from xml.sax.saxutils import escape, quoteattr 

TEST_PATH = 'tests/'
TEST_PART = 10

class Answer:
    def __init__(self):
	self.answers = {}
	self.dummys = 0
    
    def count(self):
	return len(self.answers)+self.dummys

    def addFromPost(self, post):
	if len(post):
	    for key in post:
		self.answers[key] = post[key].value
	else:
	    self.dummys += 1
	

    def readFromFile(self, file_name):
	test_file = codecs.open(file_name, "rb", encoding="utf-8")
	line = test_file.readline()
	while line:
	    key, value = line.split(' ', 1)
	    self.answers[key] = value[:-1]
	    line = test_file.readline()

    def serializeForFile(self):
	""" Serialize Answer data for saving in to file """
	ret = ""
	for key in self.answers:
	    ret += "%s %s\n"%(key, self.answers[key])
	return ret

    def serializePostForFile(self, post):
	""" Serialize POST data for saving in to file """
	ret = ""
	for key in post:
	    ret += "%s %s\n"%(key, post[key].value)
	return ret

    def getAnswersForQuestion(self, question_id):
	ret = []
	qid = "q%i_"%question_id
	qid_len = len(qid)
	for key in self.answers:
	    if qid == key[:qid_len]:
		ret.append(self.answers[key])

	return ret

class Question:
    def __init__(self, label="", hint="", points=1):
	self.label = label
	self.hint = hint
	self.answers = []
	self.points = points
	self.cache_points = None

	self.user_answers = None
	self.right_count = 0

    def setLabel(self, label):
	self.label = label

    def setHint(self, hint):
	self.hint = hint

    def setId(self, qid):
	self.qid = qid

    def resetUserAnswer():
	self.cache_points = None
	self.user_answers = None

    def getPoints(self):
	if self.user_answers == None:
	    return 0
	elif self.cache_points != None:
	    return self.cache_points

	if len(self.user_answers) != self.right_count:
	    return 0

	for answer in self.user_answers:
	    try:
		i = int(answer)
	    except:
		return 0

	    if i < len(self.answers):
		if not self.answers[i][0]:
		    return 0
	    else:
		return 0

	self.cache_points = self.points
	return self.points

    def _addAnswer(self, answer):
	self.answers.append(answer)

    def addRight(self, label):
	""" Add write answer """
	self.right_count += 1
	self._addAnswer((True, label))

    def addWrong(self, label):
	""" Add wrong answer """
	self._addAnswer((False, label))

    def applyAnswers(self, answer):
	"""
	Apply answers object to question.
	Answer can be applyed only once if nead more then call resetUserAnswer
	"""
	if self.user_answers == None:
	    self.user_answers = answer.getAnswersForQuestion(self.qid)

    def getHtmlQid(self, answer_index):
	qid = "q"+str(self.qid)+"_"
	if self.right_count > 1:
	    qid += "%i"%answer_index

	return qid

    def serializeForHtml(self, show_hint=True):
	""" Serialize Question object for display in html page """
	ret =  u'<div class="question">'
	ret += u'<div class="label">%s</div>'%self.label
	
	input_type = "radio" if self.right_count == 1 else "checkbox"
	if self.user_answers != None:
	    if show_hint or self.getPoints() == 0:
		ret += u'<div class="hint">%s</div>'%self.hint
	    i = 0
	    for answer in self.answers:
		state = "checked" if str(i) in self.user_answers  else ""
		answer_class = u"right_answer" if answer[0] else ""
		if answer_class == "":
		    if state:
			answer_class = "wrong_answer"
		    else:
			answer_class = "left_answer"
		
		ret += u'<div class="answer %s"><input type="%s" disabled  %s>%s</div>'%(answer_class, input_type, state,  escape(answer[1]))
		i += 1
	else:
	    i = 0
	    for answer in self.answers:
		qid = "qa%i_%i"%(self.qid, i)
		ret += u'<div class="answer"><input id="%s" type="%s" name="%s" value="%i"><label for="%s">%s</label></div>'%(qid, input_type, self.getHtmlQid(i), i, qid, escape(answer[1]))
		i += 1

	ret += '<div class="bottom_line">&nbsp;</div>'

	ret += '</div>'
	return ret

    def serializeForHtmlEdit(self):
	""" Serialize Question object for display in html page """
	ret =  '<div class="question"><div id="q%i">'%self.qid
	ret += u'<textarea name="q%i">%s</textarea><br>'%(self.qid, escape(self.label))
	ret += u'<textarea name="h%i">%s</textarea><br>'%(self.qid, escape(self.hint))
	ret += u'<input name="p%i" value="%i"><br>'%(self.qid, self.points)

	i = 0
	for answer in self.answers:
	    checked = "checked" if answer[0] else ""
	    ret += u'<input type="checkbox" name="r%i_%i" value="1" %s><textarea name="a%i_%i">%s</textarea><br>'%(self.qid, i, checked, self.qid, i, escape(answer[1]))
	    i += 1

	ret += '</div>'
	ret += u'<a href="javascript:addAnswer(%i)">Добавить ответ</a>'%self.qid
	ret += u'<input type="hidden" id="acount%i" name="acount%i" value="%i">'%(self.qid, self.qid, i)

	ret += '</div>'
	return ret

    def serializeToXml(self):
	""" Serialize Question object to XML"""
	ret =  '<question id="%i" label=%s hint=%s points="%s">'%(self.qid, quoteattr(self.label), quoteattr(self.hint), self.points)

	for answer in self.answers:
	    tag = "true" if answer[0] else "false"
	    ret += u'<answer right="%s">%s</answer>'%(tag, escape(answer[1]))

	ret += '</question>'
	return ret

    def serializeForFile(self):
	""" Serialize Question object for saving in to file """
	ret ="[question %i]\n"%self.points
	ret += u" %s\n"%self.label
	ret += "[hint]\n"
	ret += u" %s\n"%self.hint

	for answer in self.answers:
	    if answer[0]:
		ret += "[right]\n"
	    else:
		ret += "[wrong]\n"
	    ret += " %s\n"%answer[1]

	return ret


    def shuffle(self):
	""" Shuffle answers """
	random.shuffle(self.answers)

    def copyObject(self):
	""" Make a deep copy of question object """
	question = Question(self.label, self.hint)

	question.right_count = self.right_count
	question.points = self.points
	
	for answer in self.answers:
	    question._addAnswer(answer)
	return question

class Test:
    def __init__(self, caption=""):
	self.caption   = u"%s"%caption
	self.questions = []
	self.complete = False

    def addQuestion(self, question):
	if question:
	    question.setId(len(self.questions))
	    self.questions.append(question)

    def questionsCount(self):
	return len(self.questions)

    def rightAnsweredQuestionsCount(self):
	ret = 0
	for question in self.questions:
	    if question.getPoints() != 0:
		ret += 1
	return ret

    def setComplete(self):
	self.complete = True

    def isComplete(self):
	return self.complete

    def getRandomSubTest(self, questions_count):
	"""
	Create new Test object populated with given count of questions
	in random order
	""" 
	subtest = Test(self.caption)
	questions = self.questions[:]
	random.shuffle(questions)
	for question in questions[:questions_count]:
	    new_question = question.copyObject()
	    new_question.shuffle()
	    subtest.addQuestion(new_question)

	return subtest

    def applyAnswers(self, answer):
	"""
	Apply answers to whole test.
	"""
	for question in self.questions:
	    question.applyAnswers(answer)

    def readFromFile(self, file_name):
	"""
	Load test data from file.
	"""
	test_file = codecs.open(file_name, "rb", encoding="utf-8")
	text = u""
	line = test_file.readline()
	state = 0
	question = None
	while line:
	    key = line[:-1]
	    if   key == '[wrong]': # 1
		text = text[:-1]
		if state == 1:
		    question.addWrong(text)
		elif state == 2:
		    question.addRight(text)
		elif state == 4:
		    question.setHint(text)
		elif state == 3:
		    question.setLabel(text)
		text = u""
		state = 1
	    elif key == '[right]': # 2
		text = text[:-1]
		if state == 1:
		    question.addWrong(text)
		elif state == 2:
		    question.addRight(text)
		elif state == 4:
		    question.setHint(text)
		elif state == 3:
		    question.setLabel(text)
		text = u""
		state = 2
	    elif key[:10] == '[question ': # 3
		text = text[:-1]
		if state == 1:
		    question.addWrong(text)
		elif state == 2:
		    question.addRight(text)
		elif state == 5:
		    self.caption = text
		elif state == 4:
		    question.setHint(text)

		if question != None:
		    self.addQuestion(question)
		try:
		    points = int(key[10:-1])
		except:
		    points = 1
		
		question = Question(points=points)
		text = u""
		state = 3
	    elif key == '[hint]': # 4
		if state == 3:
		    question.setLabel(text[:-1])
		text = u""
		state = 4
	    elif key == '[caption]': # 5
		text = ""
		state = 5
	    else:
		text += u"%s"%line
	    line = test_file.readline()

	if state == 1:
	    question.addWrong(text)
	elif state == 2:
	    question.addRight(text)
	elif state == 4:
	    question.setHint(text)

	self.addQuestion(question)

	test_file.close()

    def getPoints(self):
	ret = 0
	for question in self.questions:
	    ret += question.getPoints()
	return ret

    def serializeForHtml(self, show_hint=True):
	""" Serialize Test object for display in html page """
	ret = ""
	for question in self.questions:
	    ret += question.serializeForHtml(show_hint)
	return ret

    def serializeForHtmlEdit(self):
	""" Serialize Test object for display in html page """
	ret = u'<input name="caption" value="%s"><br>'%self.caption
	for question in self.questions:
	    ret += question.serializeForHtmlEdit()
	ret += u'<input type="hidden" id="qcount" name="qcount" value="%i">'%(len(self.questions))

	return ret

    def serializeToXml(self, part=None):
	""" Serialize Test object to XML """
	ret = u'<test caption=%s parts="%i">'%(quoteattr(self.caption), int(math.ceil(len(self.questions)/float(TEST_PART)))) 
	
	if part != None:
	    part_start = part*TEST_PART 
	    part_end = part_start+TEST_PART 
	else:
	    part_start = 0 
	    part_end = len(self.questions)
	
	for question in self.questions[part_start:part_end]:
	    ret += question.serializeToXml()
	ret += u'</test>'

	return ret

    def serializeForFile(self):
	""" Serialize Test object for saving in to file """
	ret  = "[caption]\n"
	ret += u" %s\n"%self.caption
	for question in self.questions:
	    ret += question.serializeForFile()
	return ret[:-1].encode("utf-8")


def initTestSet():
    if not os.path.exists(TEST_PATH):
	os.mkdir(TEST_PATH)

class TestSet:
    """
    Add, remove, list tests from permanent storage
    """
    def __init__(self):
	"""
	Load all available test
	"""
	self.tests = {}

	files = os.listdir(TEST_PATH)
	for test_file in  files:
	    path = TEST_PATH+test_file
	    if os.path.isfile(path):
		test = Test()
		test.readFromFile(path)
		if len(test.questions):
		    self.tests[test_file] = test

    def listAll(self):
	return self.tests

    def addTest(self, test, file_name=None):
	if file_name == None:
	    file_name = os.tempnam(TEST_PATH)
	    tid = os.path.basename(file_name)
	else:
	    tid = os.path.basename(file_name)
	    file_name = TEST_PATH+tid

	test_file = open(file_name, 'wb')
	test_file.write(test.serializeForFile())
	test_file.close()

	self.tests[tid] = test

	return tid

    def replaceTest(self, test, file_name):
	self.addTest(test, file_name)


    def delTest(self, tid):
	if self.tests.has_key(tid):
	    self.tests.pop(tid)
	    path = TEST_PATH+tid
	    os.remove(path)

    def getByTid(self, file_name):
	return self.tests.get(file_name)

    def htmlLinkList(self):
	ret = ""
	for key in self.tests:
	    ret += u'<a href="/edit/%s">%s</a><a class="del" href="javascript:delTest(\'%s\')"> x</a><br>'%(key, escape(self.tests[key].caption), key)
	return ret

    def htmlSelectList(self):
	ret = '<select name="test_name">'
	for key in self.tests:
	    ret += u'<option value="%s">%s</option>'%(key, escape(self.tests[key].caption))
	ret += '</select>'

	return ret
