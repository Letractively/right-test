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


import os
import sqlite3
from datetime import datetime
import time
from test import Answer, Test

USER_PATH = 'results/'
USER_DB = USER_PATH+'index.db'

from xml.sax.saxutils import escape, quoteattr

def initStorage():
    if not os.path.exists(USER_PATH):
	os.mkdir(USER_PATH)

    db_conn = sqlite3.connect(USER_DB)
    db_cursor = db_conn.cursor()

    try:
	#Quick hack to determine that schema exists
	db_cursor.execute('SELECT id FROM users')
	db_cursor.fetchone()
    except:
	#Create schema
	print "Creating table: users"
	db_cursor.execute('CREATE TABLE users (`id` INTEGER PRIMARY KEY, `name` TEXT, `rank` TEXT, `test` TEXT, `result` INTEGER, `date` INTEGER, `sid` TEXT)')

    db_cursor.close()
    db_conn.close()

def recordsHtmlInfo():
    db_conn = sqlite3.connect(USER_DB)
    db_cursor = db_conn.cursor()

    ret = "<table>"
    #ret +=u'<tr><td>Дата</td><td>Ф. И. О</a></td><td>Результат</td></tr>\n'

    db_cursor.execute('SELECT `date`, `sid`, `name`, `rank`,`test`, `result` FROM `users` ORDER BY `date` DESC')
    for row in db_cursor:
	try:
	    date = datetime.fromtimestamp(int(row[0])).strftime("%d.%m.%Y %H:%m")
	except:
	    date = ""

        ret +=u'''<tr><td class="r_date">%s</td>
    		  <td class="r_name"><a href="/controltest/%s">%s</a><br>%s</td>
    		  <td class="r_test">%s</td>
    		  <td class="r_result">%s</td>
    		  <td class="r_report"><a href="/report/%s"><img src="/media/printer.gif"></a></td>
    		  </tr>\n'''%(date, row[1], escape(row[2]), escape(row[3]), escape(row[4]), row[5], row[1])
    ret += "</table>"

    db_cursor.close()
    db_conn.close()

    return ret

def userControlTestHtml(sid):
    path = USER_PATH+os.path.basename(sid)

    test = Test()
    if not os.path.exists(path+'/test'):
	return u"Пользователь не проходил тест"
    test.readFromFile(path+'/test')

    answer = Answer()
    if not os.path.exists(path+'/answer'):
	return u"Пользователь не оправлял ответов"
    answer.readFromFile(path+'/answer')

    test.applyAnswers(answer)

    return test.serializeForHtml(show_hint=False)


def userReport(sid):
    path = USER_PATH+os.path.basename(sid)

    test = Test()
    if not os.path.exists(path+'/test'):
	return {}
    test.readFromFile(path+'/test')

    answer = Answer()
    if not os.path.exists(path+'/answer'):
	return {}
    answer.readFromFile(path+'/answer')

    test.applyAnswers(answer)

    ret = {}
    qcount = test.questionsCount()
    ret['QUESTION_COUNT'] = str(qcount)
    aqcount = test.rightAnsweredQuestionsCount()
    ret['ANSWERED_QUESTION_COUNT'] = str(aqcount)
    ret['ANSWERED_QUESTION_COUNT_PERCENT'] = str(aqcount*100/qcount)

    ret['TEST_TITLE'] = escape(test.caption)

    db_conn = sqlite3.connect(USER_DB)
    db_cursor = db_conn.cursor()

    db_cursor.execute('SELECT `date`, `name`, `result`, `rank` FROM `users` WHERE `sid`=?', (sid,))
    for row in db_cursor:
	try:
	    date = datetime.fromtimestamp(int(row[0])).strftime("%d.%m.%Y %H:%m")
	except:
	    date = ""

        ret['DATE'] = date
        
        user_names = row[1].split(' ')
        full_user_name = user_names[0]
        for user_name in user_names[1:]:
	    if len(user_name):
		full_user_name += " "+user_name[0]+"."

        ret['USER_NAME'] = escape(full_user_name)
        ret['TEST_RESULT'] = str(row[2])
        ret['USER_RANK'] = escape(row[3])

    db_cursor.close()
    db_conn.close()

    return ret


class Storage:
    def __init__(self, sid, user_name, user_rank, test):
	self.sid = sid
	self.user_name = user_name
	self.user_rank = user_rank
	self.test = test
	self.answer = Answer()

	self.result = 0

	self.path = USER_PATH+sid
	os.mkdir(self.path)

	self.saveTest()
	self.populateIndex()

    def populateIndex(self):
	db_conn = sqlite3.connect(USER_DB)
	db_cursor = db_conn.cursor()

	db_cursor.execute('INSERT INTO `users` (`name`, `rank`, `test`, `result`, `date`, `sid`)VALUES(?, ?, ?, ?, ?, ?)', (self.user_name, self.user_rank, self.test.caption, '0', str(int(time.mktime(datetime.now().timetuple()))), self.sid))
	db_conn.commit()

	db_cursor.close()
	db_conn.close()

    def saveTest(self):
	test_file = open(self.path+'/test', 'wb')
	test_file.write(self.test.serializeForFile())
	test_file.close()

    def saveResult(self):
	db_conn = sqlite3.connect(USER_DB)
	db_cursor = db_conn.cursor()
	
	self.result = self.test.getPoints()
	db_cursor.execute('UPDATE `users` SET `result`=? WHERE `sid`=?', ( str(self.result), self.sid) )
	db_conn.commit()

	db_cursor.close()
	db_conn.close()

    def populateAnswers(self, post):
	self.answer.addFromPost(post)

	test_file = open(self.path+'/answer', 'ab')
	test_file.write(self.answer.serializePostForFile(post))
	test_file.close()
