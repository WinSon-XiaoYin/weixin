# -*- coding: utf-8 -*-

import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.gen
import tornado.httpclient

from settings import db

import tornado.options
from tornado.options import options, define

import xml.etree.ElementTree as ET

import re
import json

from random import randint

import hashlib

import os.path

import sys

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)


define('port', default=8000, type=int)


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

    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        xml_str = self.request.body
        xml = ET.fromstring(xml_str)
        toUserName = xml.find('ToUserName').text
        fromUserName = xml.find('FromUserName').text
        createTime = xml.find('CreateTime').text
        msgType = xml.find('MsgType').text

        if msgType == 'text':
            content = xml.find('Content').text
            msgId = xml.find('MsgId').text

            if u'笑话' in content:
                url = "http://www.qiushibaike.com/text/page/%d/?s=4903921" % randint(
                    1, 35)
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url)

                content = response.body.encode('utf-8').replace('\n', ' ').replace('\r', ' ').replace(
            ' ', '').replace('<br/>糗', 'flag').replace('<br/><br/>', 'start')

                contentlist = re.findall('flag.*?start(.*?)start', content)

                index = randint(0, len(contentlist)-1)
                content = contentlist[index-1].replace('<br/>', '\n')
                content = content.encode('utf-8')

            else:
                key = 'b4875784bc9d43eaa07239cecfc7f661'
                api = 'http://www.tuling123.com/openapi/api?key=' + key + '&info='

                url = api + content.encode('utf-8')
                client = tornado.httpclient.AsyncHTTPClient()
                response = yield tornado.gen.Task(client.fetch, url)
                
                dic_json = json.loads(response.body)
                content = dic_json['text']
                content = content.encode('utf-8')
            
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
        return self.write("Python say: Hello Winson")


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
