# -*- coding: utf-8 -*- 

import tornado.web
import tornado.httpserver
import tornado.ioloop

from settings import db

import tornado.options
from tornado.options import options, define

import xml.etree.ElementTree as ET

from lxml import etree

import requests

from random import randint

import hashlib

import os.path

define('port', default=80, type=int)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie('user')


class IndexHandler(BaseHandler):
    def get(self):
        print 'coming Get'
        token = 'YourToken'
        signature = self.get_argument('signature', '')
        timestamp = self.get_argument('timestamp', '')
        nonce = self.get_argument('nonce', '')
        echostr = self.get_argument('echostr', '')
        s = [token, timestamp, nonce]
        s.sort()
        sha1 = hashlib.sha1()
        map(sha1.update, s)
        hashcode = sha1.hexdigest()

        if hashcode == signature:
            return self.write(echostr)
        

    def post(self, *args, **kwargs):
        xml_str = self.request.body
        xml = ET.fromstring(xml_str)
        toUserName = xml.find('ToUserName').text
        fromUserName = xml.find('FromUserName').text
        createTime = xml.find('CreateTime').text
        msgType = xml.find('MsgType').text

        if msgType != 'text':
            reply = '''
            <xml>
            <ToUserName><![CDATA[%s]]></ToUserName>
            <FromUserName><![CDATA[%s]]></FromUserName>
            <CreateTime>%s</CreateTime>
            <MsgType><![CDATA[%s]]></MsgType>
            <Content><![CDATA[%s]]></Content>
            </xml>
            ''' % (
                fromUserName,
                toUserName,
                createTime,
                'text',
                'Unkown Format, Please check out'
            )
            return self.write(reply)

        content = xml.find('Content').text
        msgId = xml.find('MsgId').text


    	if u'笑话' in content:
	    url = "http://www.qiushibaike.com/text/page/%d/?s=4903921" % randint(1, 35)
    	    r = requests.get(url)
            tree = etree.HTML(r.text)
    	    contentlist = tree.xpath('//div[@class="article block untagged mb15"]')
            jokes = []

    	    for i in contentlist:
                content = i.xpath('div[@class="content"]/text()')
	        contentstring = ''.join(content)
    	        contentstring = contentstring.strip('\n')
    	        jokes.append(contentstring)
        
            index = randint(0, len(jokes))
    	    content = jokes[index-1]
            content = content.encode('utf-8')

	else:
    	    if type(content).__name__ == "unicode":
    	        content = content[::-1]
    	        content = content.encode('utf-8')

    	    elif type(content).__name__ == "str":
    	        print type(content).__name__
    	        content = content.decode('gbk').encode('utf-8')
    	        content = content[::-1]

    	reply = '''
    	<xml>
    	<ToUserName><![CDATA[%s]]></ToUserName>
    	<FromUserName><![CDATA[%s]]></FromUserName>
    	<CreateTime>%s</CreateTime>
    	<MsgType><![CDATA[%s]]></MsgType>
    	<Content><![CDATA[%s]]></Content>
    	</xml>
    	''' % (fromUserName, toUserName, createTime, msgType, content)
    	return self.write(reply)


class HelloHandler(BaseHandler):
    def get(self, *args, **kwargs):
        return self.write("Python say: Hello winson")


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/wechat', IndexHandler),
            (r'/winson', HelloHandler),
        ]
        settings = dict(
            cookie_secret="61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTp1o/Vo=",
            login_url="/login",
            debug=True,
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            xsrf_cookies=False,
        )
        super(Application, self).__init__(handlers, **settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    print 'Server start on port: ' + str(options.port)
    http_server.listen(options.port, '0.0.0.0')
    tornado.ioloop.IOLoop.instance().start()
