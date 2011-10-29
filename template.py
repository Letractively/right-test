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

import codecs
import os

TEMPLATE_PATH="templates/"

CSS_START_TAG = '<%CSSstart%>'
CSS_END_TAG = '<%CSSend%>'


class Template:
    def __init__(self, template):
	self.content = self.loadTemplate(template)
	self.css = ""

    def loadTemplate(self, template):
	template_file = codecs.open(TEMPLATE_PATH+os.path.basename(template), "rb", encoding="utf-8")
	content = template_file.read()
	template_file.close()
	
	css_start = content.find(CSS_START_TAG)
	css_end = content.find(CSS_END_TAG)

	if css_end > css_start > -1:
	    self.css += content[css_start+len(CSS_START_TAG):css_end]+"\n"
	    content = content[:css_start]+content[css_end+len(CSS_END_TAG):]

	return content

    def setData(self, key, data):
	self.content = self.content.replace(u'<!-- %s -->'%key, data)

    def setTemplate(self, key, template):
	self.setData(key, self.loadTemplate(template))

    def show(self):
	self.content = self.content.replace( '<%CSS%>', self.css )
	
	return self.content
