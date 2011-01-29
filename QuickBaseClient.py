############################################################################
#Copyright (c) 2009-2011 Seemant Kulleen
# Released under the MIT license.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy 
# of this software and associated documentation files (the "Software"), to deal 
# in the Software without restriction, including without limitation the rights 
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
# copies of the Software, and to permit persons to whom the Software is 
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE 
# SOFTWARE. 
############################################################################


import pycurl
from lxml import etree as ET
from lxml.builder import E


try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


class QuickBaseClient( object ):
    base_url = 'https://www.quickbase.com/db/'
    header = ['Content-Type: application/xml',]
    active_db = ''

    userid = None
    auth_ticket = None
    token  = None
    tables = {}


    def __init__( self, username=None, password=None, token=None, app=None ):
        if username is None or password is None:
            raise Exception, "Username and password can not be blank."

        if token is None:
            raise Exception, "Please generate an application token in QuickBase."

        if app is None:
            raise Exception, "Please specify a QuickBase Application."

        self.username = username
        self.password = password
        self.token = token

        self.cxn = pycurl.Curl()
        self.cxn.setopt(pycurl.POST, 1)

        self.authenticate()
        
        self.set_application(app=app)
        self.database()


    def connect( self, db='', xml=None, api=None ):
        header = list(self.header)

        if not db:
            db = self.active_db


        uri = '%s/%s' % (self.base_url, db)

        header.append("QUICKBASE-ACTION: " + api)
        self.cxn.setopt(pycurl.URL, uri)
        self.cxn.setopt(pycurl.HTTPHEADER, header)
        s = StringIO()

        self.cxn.setopt(pycurl.WRITEFUNCTION, s.write)
        self.cxn.setopt(pycurl.POSTFIELDS, ET.tostring(xml, pretty_print=True))
        self.cxn.perform()
        resp = ET.XML(s.getvalue())

        # If the authentication period has timed out, then reauthenticate
        # and rerun the original connection request
        if resp.findtext('errcode') == '22':
            self.authenticate()
            resp = self.connect(db=db, xml=xml, api=api)
        else:
            if resp.findtext('errcode') != '0':
                raise Exception, resp.findtext('errtext')

        return resp


    def clear_flags( self, db='' ):
        header = list(self.header)
        if not db:
            db = self.active_db

        uri = '%s/%s?act=QBI_ClearFlags' % (self.base_url, db)
        self.cxn.setopt(pycurl.URL, uri)
        self.cxn.setopt(pycurl.HTTPHEADER, header)

        self.cxn.perform()
        return


    def authenticate( self ):
        api = 'API_Authenticate'
        db = 'main'

        xml = (
            E.qdbapi(
                E.username(self.username),
                E.password(self.password),
                E.hours('24')
            )
        )

        creds = self.connect(db=db, xml=xml, api=api)

        self.userid = creds.findtext('userid')
        self.auth_ticket = creds.findtext('ticket')

        return

    

    def get_dbid( self, app='' ):
        api = 'API_FindDBByName'
        db = 'main'

        xml = (
            E.qdbapi(
                E.ticket(self.auth_ticket),
                E.dbname(app),
            )
        )

        return self.connect(db=db, xml=xml, api=api)


    def set_application( self, app='' ):
        response = self.get_dbid(app=app)
        self.active_db = '%s' % response.findtext('dbid')
        return


    def database( self, db='' ):
        schema = self.get_schema(db=db)
        for element in schema.findall('table/chdbids/chdbid'):
            self.tables[element.values()[0][len('_dbid_'):]] = element.text

        return


    def get_schema( self, db='' ):
        api = 'API_GetSchema'
        xml = (
            E.qdbapi(
                E.ticket(self.auth_ticket),
                E.apptoken(self.token),
            )
        )

        schema = self.connect(db=db, xml=xml, api=api)

        return schema


    def get_record( self, db=None, number='' ):
        api = 'API_DoQuery'
        
        if not db:
            db = self.active_db

        schema = self.get_schema(db=db)

        for node in schema.findall('table/fields/field'):
            if node.attrib['field_type'] == 'recordid':
                field = node.attrib['id']
                break

        query = "{'%s'.EX.'%s'}" % (field, number)

        xml = (
            E.qdbapi(
                E.ticket(self.auth_ticket),
                E.apptoken(self.token),
                E.query(query),
            )
        )

        return self.connect(db=db, xml=xml, api=api)


    def get_changed_records( self, db=None, clear=False ):
        api = 'API_DoQuery'

        if not db:
            db = self.active_db

        options = 'sortorder-A.onlynew'

        xml = (
            E.qdbapi(
                E.ticket(self.auth_ticket),
                E.apptoken(self.token),
                E.options(options),
            )
        )

        response = self.connect(db=db, xml=xml, api=api)

        # Now, clear the flags
        if clear:
            self.clear_flags(db=db)


        return response

