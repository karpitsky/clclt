#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
#
# calculate bot (http://twitter.com/clclt)
#
# Copyright (C) 2011 Michael Karpitsky <michael.karpitsky@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os
import json
import urllib2
import gzip
import StringIO
import time
import datetime
import rfc822
import random
import oauth2 as oauth
from math import *
from settings import *

class TwitterHandler:
    def __init__(self, num=0):
        if (TOKEN_KEY[num] and TOKEN_SECRET[num]):
            self._signature_method_plaintext = oauth.SignatureMethod_PLAINTEXT()
            self._signature_method_hmac_sha1 = oauth.SignatureMethod_HMAC_SHA1()
            self._oauth_token    = oauth.Token(key=TOKEN_KEY[num], secret=TOKEN_SECRET[num])
            self._oauth_consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
        else:
            exit()

    def UsersLookup(self, user_id):
        url = 'https://api.twitter.com/1/users/lookup.json'
        data = {}
        parameters = {}
        uids = list()
        uids.extend(user_id)
        parameters['user_id'] = ','.join(["%s" % u for u in uids])
        _json = self._FetchUrl(url, parameters=parameters)
        print _json
        data = json.loads(_json)
        error = self._ParseError(data)
        if error is not None:
            print error
            exit()
        return [self._ParseResult(u) for u in data]

    def GetFollowerIDs(self, cursor=-1):
        url = 'https://api.twitter.com/1/followers/ids.json' 
        parameters = {}
        parameters['cursor'] = cursor
        parameters['user_id'] = USERID
        _json = self._FetchUrl(url, parameters=parameters)
        data = json.loads(_json)
        error = self._ParseError(data)
        if error is not None:
            print error
            exit()
        return data

    def PostDirectMessage(self, user, text):
        url  = 'https://api.twitter.com/1/direct_messages/new.json'
        data = {'text': text, 'user': user}
        _json = self._FetchUrl(url, post_data=data)
        print data
        print _json
        return _json

    def PostUpdate(self, status):
        url = 'https://api.twitter.com/1/statuses/update.json'
        u_status = unicode(status, 'utf-8')
        data = {'status': status}
        _json = self._FetchUrl(url, post_data=data)
        return _json

    def _ParseError(self, data):
        try:
            error = data.get('error', None)
        except:
            error = None
        return error

    def _ParseResult(self, user):
        data = {}
        data['id'] = user.get('id', None)
        data['screen_name'] = user.get('screen_name', None)
        data['created_at'] = user.get('created_at', None)
        data['statuses_count'] = user.get('statuses_count', None)
        data['followers_count'] = user.get('followers_count', None)
        return data

    def _FetchUrl(self, url, post_data=None, parameters=None):
        if post_data:
            http_method = "POST"
        else:
            http_method = "GET"

        opener = urllib2.OpenerDirector()
        opener.add_handler(urllib2.HTTPHandler())
        opener.add_handler(urllib2.HTTPSHandler())

        if not post_data:
            opener.addheaders.append(('Accept-Encoding', 'gzip'))

        if http_method == "POST":
            parameters = post_data.copy()

        req = oauth.Request.from_consumer_and_token(self._oauth_consumer,
                                                    token=self._oauth_token,
		                                    http_method=http_method,
                                                    http_url=url, parameters=parameters)

        req.sign_request(self._signature_method_hmac_sha1, self._oauth_consumer, self._oauth_token)

        if http_method == "POST":
            encoded_post_data = req.to_postdata()
        else:
            encoded_post_data = None
            url = req.to_url()

        try:
            response = opener.open(url, encoded_post_data)
            url_data = self._UnGzip(response)
        except urllib2.HTTPError, e:
            print e
        opener.close()

        return url_data

    def _UnGzip(self, response):
        data = response.read()
        if response.headers.get('content-encoding', None) == 'gzip':
            compressedstream = StringIO.StringIO(data) 
            url_data = gzip.GzipFile(fileobj=compressedstream).read()
        else:
            url_data = data
        return url_data

class FilesHandler:
    def get_json_from_file(self, file, user_file=0):
        try:
            json_data = open(file)
            try:
                data = json.load(json_data)
                if user_file == 1:
                    data['sub'] = data.get("sub", "follow")
                    data['dm'] = data.get("dm", "public")
                    for i in ["y", "f", "s"]:
                        if i in data:
                            pass
                        else:
                            data[i] = 0
            except:
                data = {}
                data['sub'] = "follow"
                data['dm'] = "public"
                data['y'] = 0
                data['s'] = 0
                data['f'] = 0
            json_data.close()
        except:
            print "get_json_from_file error"
            exit()
        return data
    
    def get_user_info(self, user_id):
        user_file = ROOT_PATH + '/data/' + str(user_id) + ".json"
        if not os.path.exists(user_file):
            open(user_file, 'w').close()
        return self.get_json_from_file(user_file, 1)

    def save_info_to_file(self, user_id, user_data):
        user_file = ROOT_PATH + '/data/' + str(user_id) + ".json"
        try:
            file = open(user_file, 'w')
            data = json.dumps(user_data)
            file.write(data)
            file.close()
        except:
            exit()
        return True

    def save_ids(self, ids_file, ids):
        file = open(ids_file, 'w')
        data = json.dumps(ids)
        file.write(data)
        file.close()
        return True

    def get_template(self, template_type, user_name, number, lang=LANG):
        template_file = TEMPLATE_PATH + template_type + "_" + lang + ".data"
        if template_type == "birthday":
            y = ("", '1 год', '2 года', '3 года', '4 года', '5 лет', '6 лет', '7 лет', '8 лет', '9 лет', '10 лет')
            number = y[number]
        lines = open(template_file).read().splitlines()
        line = random.choice(lines)
        user_name = user_name.encode('ascii','ignore')
        return line % (user_name, number)

class Calculate:
    def __init__(self):
        ids_file = ROOT_PATH + '/ids.json'
        self.fh = FilesHandler()
        self.th = TwitterHandler()
        self.th_w = TwitterHandler()
        self.requests = 0
        self.bot = 0
        self.ids = self.fh.get_json_from_file(ids_file)
        followersIDs = self.th.GetFollowerIDs()
        self.requests += 1
        add_new = 0
        for follower in followersIDs:
            there_is = 0
            for user in self.ids:
                if follower == user:
                    there_is = 1
                    break
            if there_is == 0:
                add_new = 1
                self.ids.append(follower)
        if add_new == 1:
            self.fh.save_ids(ids_file, self.ids)

    def do_calculate(self):
        users_count = len(self.ids)
        req_count = ceil(users_count/100.0)
        i = 0
        while i < req_count:
            mod_req = self.requests % 200
            if mod_req == 0:
                self.bot += 1
                self.th = TwitterHandler(self.bot)
            part_of_100_ids = self.ids[(i*100):(((i+1)*100)-1)]
            part_of_100_data = self.th.UsersLookup(user_id=part_of_100_ids)
            self.requests += 1
            for user in part_of_100_data:
                user_data = self.fh.get_user_info(user['id'])
                if user_data['sub'] != "nofollow":
                    self.checking_birthday(user, user_data)
                    self.checking_statuses(user, user_data)
                    self.checking_followers(user, user_data)
            i += 1
            
    def checking_birthday(self, user, user_data):
        parse_created_at = rfc822.parsedate(user['created_at'])
        dt = datetime.datetime.now()
        if dt.strftime('%m%d') == time.strftime("%m%d", parse_created_at):
            check = int(dt.strftime('%Y')) - int(time.strftime("%Y", parse_created_at))
        else:
            check = 0
        self._post("y", check, user, user_data)

    def checking_statuses(self, user, user_data):
        check = self._roundness(user['statuses_count'], user['id'], 900)
        self._post("s", check, user, user_data)

    def checking_followers(self, user, user_data):
        check = self._roundness(user['followers_count'], user['id'], 100)
        self._post("f", check, user, user_data)

    def _roundness(self, number, user, min, indent=8):
        if number > min:
            i = 0
            length_mod = len(str(number))
            mod = "1" + "0"*(length_mod - 1)
            mod = int(mod)
            while i < indent:
                i += 1
                result = number + i
                is_round = result % mod
                if is_round == 0:
                    return result
        return False

    def _post(self, type, check, user, user_data):
        if check:
            user_id = user['id']
            if check != user_data[type]:
                if type == "s":
                    template = "statuses"
                elif type == "f":
                    template = "followers"
                elif type == "y":
                    template = "birthday"
                user_data[type] = check
                self.fh.save_info_to_file(user_id, user_data)
                message = self.fh.get_template(template, user['screen_name'], check)
                if user_data['dm'] == "private":
                    self.th_w.PostDirectMessage(user_id, message)
                else:
                    self.th_w.PostUpdate(message)


if __name__ == '__main__':
    c = Calculate()
    c.do_calculate()

# vim: tabstop=4 expandtab shiftwidth=4 softtabstop=4

