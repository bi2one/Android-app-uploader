#! /usr/bin/python
# -*- encoding: utf-8 -*-

import json, sys, getopt, upload, pprint
from UploadStates import *

import sys
import getopt

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

def main(argv=None):
    """
    Android market uploader
    
    -h, --help                  show this help page
    -j, --json=[json_file]      upload / update app by json file
    -u, --username=[market_id]  market id
    -p, --password=[password]   market password
    """
    
    if argv is None:
        argv = sys.argv
    try:
        try:
            opts, args = getopt.getopt(argv[1:], "hj:u:p:", ["help", "json=", "username=", "password="])
        except getopt.error, msg:
             raise Usage(msg)
    except Usage, err:
        print >>sys.stderr, err.msg
        print >>sys.stderr, "for help use --help"
        return 2

    username = get_arg(opts, ('-u', '--username'))
    password = get_arg(opts, ('-p', '--password'))

    if None in (username, password):
        print >>sys.stderr, "You must specify username and password."
        print main.__doc__
        return 2
                       
    for o, a in opts:
        if o in ("-h", "--help"):
            print main.__doc__
            return 0
        elif o in ("-j", "--json"):
            return upload_json(a, username, password)
    print >>sys.stderr, "for help use --help"
    return 2

def get_arg(opts, opt_names):
    try:
        return [opt[1] for opt in opts if opt[0] in opt_names][0]
    except IndexError:
        return None

def upload_json(file_path, username, password):
    try:
        contents = json.loads(open(file_path).read())
    except Exception, msg:
        print >>sys.stderr, msg
        return 2
    
    print "[login] %s" % (username)
    try:
        uploader = upload.AndroidUploader(username, password)
    except upload.LoginFailedError as e:
        print >>sys.stderr, e
        return 2
        
    for item in contents:
        print "[%s] %s..." % (item['type'], item['apk'])
        if item['type'] == 'upload':
            ret_code = uploader.upload(item['apk'],
                                       item['screenshots'],
                                       item['icon'],
                                       map(lambda e: upload.LanguageElement(e['language'], e['title'], e['description']), item['languageElements']),
                                       item['app_type'],
                                       item['category'],
                                       item['contentsLevel'],
                                       item['webpage'],
                                       item['email'])
        else:
            ret_code = uploader.update(item['package'], item['apk'])
            
        if ret_code == upload.RET_STOP:
            print >>sys.stderr, "[STOPED] stopped. Check the log for more information."
            return 2
        else:
            print "[PASSED] pass apk. Check the log for more information."
    return 0
        
if __name__ == "__main__":
    sys.exit(main())
