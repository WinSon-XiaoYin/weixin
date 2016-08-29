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

from lxml import etree

import requests
import re
import json

from random import randint

import hashlib

import os.path

import urllib
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

    def tryFind(self, html):
        try:
            city = re.findall('<city>(.*?)</city>', html)[0].encode('utf-8')
            return True
        except Exception, e:
            return False

    @tornado.web.asynchronous
    @tornado.gen.engine
    def post(self, *args, **kwargs):
        xml_str = self.request.body
        xml = ET.fromstring(xml_str)
        toUserName = xml.find('ToUserName').text
        fromUserName = xml.find('FromUserName').text
        createTime = xml.find('CreateTime').text
        msgType = xml.find('MsgType').text

        if msgType != 'text':
            text = '1、回复城市名称，可以查询该城市当日天气情况' + '\n' + '如：武汉' + \
                '\n' + ' ' + '\n' + '2、回复笑话，可以收到最新笑话' + '\n' + '如：笑话'
            text = text.encode('utf-8')
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
                text,
            )
            return self.write(reply)

        content = xml.find('Content').text
        msgId = xml.find('MsgId').text

        url = 'http://wthrcdn.etouch.cn/WeatherApi?city=%s' % content
        html = requests.get(url).content

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

        elif self.tryFind(html):
            city = re.findall('<city>(.*?)</city>', html)[0].encode('utf-8')
            wendu = re.findall('<wendu>(.*?)</wendu>', html)[0].encode('utf-8')
            shidu = re.findall('<shidu>(.*?)</shidu>', html)[0].encode('utf-8')

            try:
                aqi = re.findall('<aqi>(.*?)</aqi>', html)[0].encode('utf-8')
                pm25 = re.findall(
                    '<pm25>(.*?)</pm25>', html)[0].encode('utf-8')
                suggest = re.findall(
                    '<suggest>(.*?)</suggest>', html)[0].encode('utf-8')
                quality = re.findall(
                    '<quality>(.*?)</quality>', html)[0].encode('utf-8')
                o3 = re.findall('<o3>(.*?)</o3>', html)[0].encode('utf-8')
                co = re.findall('<co>(.*?)</co>', html)[0].encode('utf-8')
                pm10 = re.findall(
                    '<pm10>(.*?)</pm10>', html)[0].encode('utf-8')
                so2 = re.findall('<so2>(.*?)</so2>', html)[0].encode('utf-8')
                no2 = re.findall('<no2>(.*?)</no2>', html)[0].encode('utf-8')
                flag = 1
            except Exception, e:
                flag = 0

            date = re.findall('<date>(.*?)</date>', html)
            high = re.findall('<high>(.*?)</high>', html)
            low = re.findall('<low>(.*?)</low>', html)

            Type = re.findall('<type>(.*?)</type>', html)
            fengxiang = re.findall('<fengxiang>(.*?)</fengxiang>', html)
            fengli = re.findall('<fengli>(.*?)</fengli>', html)

            content_1 = "城市：" + city + "\n" + date[0].encode('utf-8') + "\n" + \
                "温度：" + wendu + "℃" + "\n" + high[0].encode('utf-8') + "\n" + \
                low[0].encode('utf-8') + "\n" + " " + "\n" + \
                "白天：" + Type[0].encode('utf-8') + " " + fengxiang[1].encode('utf-8') + " " + \
                fengli[1].encode('utf-8') + "\n" + \
                "晚上：" + Type[1].encode('utf-8') + " " + fengxiang[2].encode('utf-8') + " " + \
                fengli[2].encode('utf-8') + " " + "\n"

            if flag == 1:
                content_2 = "\n" + "空气质量指数：" + aqi + "\n" + "湿度：" + shidu + "\n" + "pm2.5：" + \
                    pm25 + "\n" + "空气质量：" + quality + "\n" + "臭氧：" + \
                    o3 + "\n" + "一氧化碳：" + co + "\n" + \
                    "颗粒物(PM10)：" + pm10 + "\n" + "二氧化硫：" + so2 + \
                         "\n" + "二氧化氮：" + no2 + "\n" + "建议：" + suggest

                content = content_1 + content_2
            else:
                content = content_1

        else:
            key = '8b005db5f57556fb96dfd98fbccfab84'
            api = 'http://www.tuling123.com/openapi/api?key=' + key + '&info='

            request = api + content.encode('utf-8')
            page = urllib.urlopen(request)
            html = page.read()
            dic_json = json.loads(html)
            content = '小银: '.decode('utf-8') + dic_json['text']
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

    @tornado.web.asynchronous
    @tornado.gen.engine
    def get(self, *args, **kwargs):
        # url = 'http://wthrcdn.etouch.cn/WeatherApi?city=%s' % u'武汉'
        url = "http://www.qiushibaike.com/text/page/1/?s=4903921"

        # sync
        # http_request = tornado.httpclient.HTTPRequest(url, method='GET')
        # synClient = tornado.httpclient.HTTPClient()
        # response = synClient.fetch(http_request)

        # async
        client = tornado.httpclient.AsyncHTTPClient()
        response = yield tornado.gen.Task(client.fetch, url)

        content = response.body.encode('utf-8').replace('\n', ' ').replace('\r', ' ').replace(
            ' ', '').replace('<br/>糗', 'flag').replace('<br/><br/>', 'start')

        contentlist = re.findall('flag.*?start(.*?)start', content)

        index = randint(0, len(contentlist)-1)
        print contentlist[index].replace('<br/>', '\n')


        # xml = ET.fromstring(response.body)
        # print url
        # fengli = xml.find('fengli').text
        # print fengli

        self.write("Python say: Hello Winson")
        self.finish()


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
