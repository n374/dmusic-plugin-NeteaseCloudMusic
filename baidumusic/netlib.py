#! /usr/bin/env python
# -*- coding: utf-8 -*-

import pycurl
import StringIO
from  urllib import urlencode

class Curl(object):
    '''
    methods:
    
    GET
    POST
    UPLOAD
    '''
    HEADERS = ['User-agent: Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1)',]

    
    def __init__(self, cookie_file=None, headers=HEADERS):
        self.cookie_file = cookie_file
        self.headers = headers
        self.url = ""
    
    def request(self, url, data=None, method="GET", header=None, proxy_host=None, proxy_port=None):
        '''
        open url width get method
        @param url: the url to visit
        @param data: the data to post
        @param header: the http header
        @param proxy_host: the proxy host name
        @param proxy_port: the proxy port
        '''
        if isinstance(url, unicode):
            self.url = str(url)
        else:    
            self.url = url
        
        crl = pycurl.Curl()
        #crl.setopt(pycurl.VERBOSE,1)
        crl.setopt(pycurl.NOSIGNAL, 1)

        # set proxy
        if proxy_host:
            crl.setopt(pycurl.PROXY, proxy_host)
        if proxy_port:
            crl.setopt(pycurl.PROXYPORT, proxy_port)
            
        if self.cookie_file:    
            crl.setopt(pycurl.COOKIEJAR, self.cookie_file)            
            crl.setopt(pycurl.COOKIEFILE, self.cookie_file)            
            
        # set ssl
        crl.setopt(pycurl.SSL_VERIFYPEER, 0)
        crl.setopt(pycurl.SSL_VERIFYHOST, 0)
        crl.setopt(pycurl.SSLVERSION, 3)
         
        crl.setopt(pycurl.CONNECTTIMEOUT, 10)
        crl.setopt(pycurl.TIMEOUT, 300)
        crl.setopt(pycurl.HTTPPROXYTUNNEL, 1)

        headers = self.headers or header
        if headers:
            crl.setopt(pycurl.HTTPHEADER, headers)

        crl.fp = StringIO.StringIO()
            
        if method == "GET" and data:    
            self.url = "%s?%s" % (self.url, urlencode(data))
            
        elif method == "POST" and data:
            crl.setopt(pycurl.POSTFIELDS, urlencode(data))  # post data
            
        elif method == "UPLOAD" and data:
            if isinstance(data, dict):
                upload_data = data.items()
            else:
                upload_data = data
            crl.setopt(pycurl.HTTPPOST, upload_data)   # upload file
            
        crl.setopt(pycurl.URL, self.url)
        crl.setopt(crl.WRITEFUNCTION, crl.fp.write)
        try:
            crl.perform()
        except Exception:
            return None
        
        crl.close()
        back = crl.fp.getvalue()
        crl.fp.close()
        return back
    
