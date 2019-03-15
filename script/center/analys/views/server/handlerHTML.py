# !/usr/bin/env python
# -*- coding: utf-8 -*-

from HTMLParser import HTMLParser


class HTMLChange(HTMLParser):

    color = False
    addU = False
    addP = False
    addEm = False
    content = ''

    def handle_starttag(self, tag, attrs):
        if tag == 'u':
            self.content += '<u>'
            self.addU = True
        if tag == 'p':
            self.addP = True
        if tag == 'em':
            self.content += '<em>'
            self.addEm = True

        for attr in attrs:
            if attr[0] == "style" and tag == 'span':
                if attr[1][0:5] == "color":
                    self.content += '<font color="%s">' % attr[1][6:13]
                    self.color = True

    def handle_endtag(self, tag):
        if tag == 'u' and self.addU:
            self.content += '</u>'
            self.addU = False
        elif tag == 'span' and self.color:
            self.content += '</font>'
            self.color = False
        elif tag == 'p' and self.addP:
            self.content += '<br />'
            self.addP = False
        elif tag == 'em' and self.addEm:
            self.content += '</em>'
            self.addEm = False


    def handle_startendtag(self, tag, attrs):
        """
        recognize tag that without endtag, like <img />
        :param tag:
        :param attrs:
        :return:
        """
        if tag == 'br':
            self.content += '<br />'

    def handle_data(self, data):
        if data:
            self.content += data
