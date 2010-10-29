# -*- coding: utf-8 -*-

import subprocess
import os
from xml.dom import minidom, DOMException
import codecs

class tit:
    """ This class controls all lists and items """
    lists = []
    current_list = None

    @staticmethod
    def load(filename=None):
        """ Loads the todo list from the default location or from 
        the specified filename """
        if not filename:
            filename = '%s/.tit/data.xml' % os.getenv('HOME')

        xml = open(filename, 'rb').read()

        xmldoc = minidom.parseString(xml)
        t = tit()

        for rootNodes in xmldoc.childNodes:
            for child in rootNodes.childNodes:
                if child.nodeType == 1:
                    if child.tagName == 'current' and child.getAttribute('list'):
                        t.current_list = child.getAttribute('list')
                    elif child.tagName == 'list' and child.getAttribute('name'):
                        items = []
                        for todo in child.childNodes:
                            if todo.nodeType == 1:
                                comments = []

                                for c in todo.childNodes:
                                    if c.nodeType == 1 and c.nodeName == 'comment':
                                        comments.append(comment(int(c.getAttribute('id')), c.childNodes[0].data))

                                id = int(todo.getAttribute('id'))
                                priority = int(todo.getAttribute('priority'))
                                name = todo.getAttribute('name')
                                i = item(id, priority, name, comments=comments)

                                items.append(i)

                        id = int(child.getAttribute('id'))
                        name = child.getAttribute('name')
                        desc = child.getAttribute('description')
                        l = list(id, name, description=desc, items=items)

                        l.sort()
                        t.add(new_list=l)

        current_list_found = False
        for l in t.lists:
            if l.name == t.current_list:
                t.current_list = l
                current_list_found = True

        if not current_list_found:
            raise DOMException('test')

        return t

    def save(self, filename=None):
        if not filename:
            filename = '%s/.tit/data.xml' % os.getenv('HOME')

        xmldoc = minidom.getDOMImplementation().createDocument(None, 'tit', None)

        curr = xmldoc.createElement('current')
        curr.setAttribute('list', self.current_list.name)
        xmldoc.documentElement.appendChild(curr)

        for l in self.lists:
            list_xml = xmldoc.createElement('list')
            list_xml.setAttribute('name', (l.name))
            list_xml.setAttribute('id', str(l.id))
            list_xml.setAttribute('description', l.description)
            for i in l.items:
                item_xml = xmldoc.createElement('item')
                item_xml.setAttribute('id', str(i.id))
                item_xml.setAttribute('name', i.name)
                item_xml.setAttribute('priority', str(i.priority))

                for c in i.comments:
                    comment_xml = xmldoc.createElement('comment')
                    comment_text_xml = xmldoc.createTextNode(c.text)
                    comment_xml.setAttribute('id', str(c.id))
                    comment_xml.appendChild(comment_text_xml)
                    item_xml.appendChild(comment_xml)

                list_xml.appendChild(item_xml)
            xmldoc.documentElement.appendChild(list_xml)

        xmldoc.writexml(codecs.open(filename, 'wb', 'utf-8'), encoding='utf-8')

    def add(self, new_list=None, new_name=None, new_description=u''):
        if new_list and not new_name:
            if len(self.lists):
                sorted(self.lists, key=lambda i: i.id)
                new_list.id = self.lists[-1].id + 1
            else:
                new_list.id = 0
            self.lists.append(new_list)
        elif not new_list and new_name:
            self.add(new_list=list(0, new_name, new_description))

    def find(self, name=None, id=None):
        for l in self.lists:
            if name and l.name == name:
                return l
            elif id is not None and l.id == int(id):
                return l

    def rm(self, rm_list=None, rm_name=None, rm_id=None):
        if rm_list:
            self.lists.remove(rm_list)
        elif rm_name:
            self.rm(rm_list=self.find(name=rm_name))
        elif rm_id:
            self.rm(rm_list=self.find(id=rm_id))

    def list(self):
        output_string = []

        for l in self.lists:
            output_string.append(l.list(current= l==self.current_list))

        return '\n\n'.join(output_string)

class list:
    """ This class defines todo lists"""
    name = u''
    _git_branch = None
    items = []
    id = 0
    description = u''

    def __init__(self, id, name, description=u'', new_branch=False, branch_prefix=None, items=[]):
        self.id = id
        self.name = name
        self.description = description
        self.items = items

        if new_branch:
            self._git_branch = '%s%s%s' % (branch_prefix, '-' if branch_prefix else '', name)

    def __unicode__(self):
        return self.name

    def sort(self):
        self.items.sort(key=lambda i: i.priority, reverse=True)
        for i in self.items:
            i.sort()

    def switch(self):
        """ This method switches git branches if possible """
        if self._git_branch:
            p = subprocess.Popen('git checkout %s' % self._git_branch)

    def list(self, current=False):
        """ This method lists the items in this list """

        output_string = []

        if current:
            output_string.append('$INFO---------- CURRENT ----------$CLEAR')

        output_string.append('$ID#%s$CLEAR $LIST%s$CLEAR %s' % (self.id, self.name, self.description))

        for item in self.items:
            output_string.append('\t%s' % item.__unicode__())
            for c in item.comments:
                output_string.append('\t\t$ID#%s$CLEAR %s' % (c.id, c.text))

        if current:
            output_string.append('$INFO---------- CURRENT ----------$CLEAR')

        return '\n'.join(output_string)

    def find(self, name=None, id=None):
        """ Finds an item in this list with specified name """
        for item in self.items:
            if name and item.name == name:
                return item
            if id is not None and item.id == int(id):
                return item

    def add(self, new_item=None, new_name=None, new_priority=None):
        """ This method adds items to this list """
        if new_item:
            if len(self.items):
                self.items.sort(key=lambda i: i.id)
                new_item.id = 1 + self.items[-1].id
            else:
                new_item.id = 0

            self.items.append(new_item)

            self.sort()
        elif new_name:
            self.add(new_item=item(0, new_priority if new_priority else 2, new_name))

    def rm(self, rm_item=None, rm_name=None, rm_id=None):
        """ This method removes item from this list """
        if rm_item:
            self.items.remove(rm_item)
        elif rm_name:
            self.rm(self.find(name=rm_name))
        elif rm_id:
            self.rm(self.find(id=rm_id))

class item:
    """ This class defines todo list items """
    name = u''
    priority = 2
    id = 0
    comments = []

    def __init__(self, id, priority, name, comments=[]):
        self.id = id
        self.priority = priority
        self.name = name
        self.comments = comments

    def __unicode__(self):
        return '$ID#%s$CLEAR $%sITEM-%s-$CLEAR $ITEM%s$CLEAR' % (self.id, self.priority, self.priority, self.name)

    def sort(self):
        self.comments.sort(key=lambda c: c.id, reverse=True)

    def find(self, id=None, text=None):
        for c in self.comments:
            if id and c.id == int(id):
                return c
            elif text and c.text == text:
                return c

    def add(self, new_text=None, new_comment=None):
        if new_comment:
            if len(self.comments):
                new_comment.id = self.comments[0].id
            else:
                new_comment.id = 0

            self.comments.append(new_comment)
            self.sort()
        elif new_text:
            self.add(new_comment=comment(0, new_text))

    def rm(self, rm_id=None, rm_text=None):
        if rm_id:
            self.comments.remove(self.find(id=rm_id))
        else:
            self.comments.remove(self.find(text=rm_text))

class comment:
    """ This class defines comments for todo items """
    text = u''
    id = 0

    def __init__(self, id, text):
        self.id = id
        self.text = text
