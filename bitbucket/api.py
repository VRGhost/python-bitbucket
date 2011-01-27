#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Bitbucket API wrapper.  Written to be somewhat like py-github:

https://github.com/dustin/py-github

"""

from urllib2 import Request, urlopen
from urllib import urlencode
from functools import wraps

try:
    import json
except ImportError:
    import simplejson as json

api_base = 'https://api.bitbucket.org/1.0/'
api_toplevel = 'https://api.bitbucket.org/'

class AuthenticationRequired(Exception):
    pass

def requires_authentication(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        username = self.bb.username if hasattr(self, 'bb') else self.username
        password = self.bb.password if hasattr(self, 'bb') else self.password
        if not all((username, password)):
            raise AuthenticationRequired("%s requires authentication" % method.__name__)
        return method(self, *args, **kwargs)
    return wrapper

def smart_encode(**kwargs):
    """Urlencode's provided keyword arguments.  If any kwargs are None, it does
    not include those."""
    args = dict(kwargs)
    for k,v in args.items():
        if v is None:
            del args[k]
    if not args:
        return ''
    return urlencode(args)


class BitBucket(object):
    """Main bitbucket class.  Use an instantiated version of this class
    to make calls against the REST API."""
    def __init__(self, username='', password=''):
        self.username = username
        self.password = password
        # extended API support

    def build_request(self, url):
        if not all((self.username, self.password)):
            return Request(url)
        auth = '%s:%s' % (self.username, self.password)
        auth = {'Authorization': 'Basic %s' % (auth.encode('base64').strip())}
        return Request(url, None, auth)

    def load_url(self, url, quiet=False):
        request = self.build_request(url)
        try:
            result = urlopen(request).read()
        except:
            if not quiet:
                import traceback
                traceback.print_exc()
                print "url was: %s" % url
            result = "[]"
        return result

    def user(self, username):
        return User(self, username)

    def repository(self, username, slug):
        return Repository(self, username, slug)

    @requires_authentication
    def emails(self):
        """Returns a list of configured email addresses for the authenticated user."""
        url = api_base + 'emails/'
        return json.loads(self.load_url(url))

class User(object):
    """API encapsulation for user related bitbucket queries."""
    def __init__(self, bb, username):
        self.bb = bb
        self.username = username

    def repository(self, slug):
        return Repository(self.bb, self.username, slug)

    def repositories(self):
        user_data = self.get()
        return user_data['repositories']

    def events(self):
        url = api_base + 'users/%s/events/' % self.username
        return json.loads(self.bb.load_url(url))

    def get(self):
        url = api_base + 'users/%s/' % self.username
        return json.loads(self.bb.load_url(url))

    def __repr__(self):
        return '<User: %s>' % self.username

class Repository(object):
    def __init__(self, bb, username, slug):
        self.bb = bb
        self.username = username
        self.slug = slug
        self.base_url = api_base + 'repositories/%s/%s/' % (self.username, self.slug)

    def get(self):
        return json.loads(self.bb.load_url(self.base_url))

    def changeset(self, revision):
        """Get one changeset from a repos."""
        url = self.base_url + 'changesets/%s/' % (revision)
        return json.loads(self.bb.load_url(url))

    def changesets(self, limit=None):
        """Get information about changesets on a repository."""
        url = self.base_url + 'changesets/'
        query = smart_encode(limit=limit)
        if query: url += '?%s' % query
        return json.loads(self.bb.load_url(url, quiet=True))

    def tags(self):
        """Get a list of tags for a repository."""
        url = self.base_url + 'tags/'
        return json.loads(self.bb.load_url(url))

    def branches(self):
        """Get a list of branches for a repository."""
        url = self.base_url + 'branches/'
        return json.loads(self.bb.load_url(url))

    def issue(self, number):
        return Issue(self.bb, self.username, self.slug, number)

    def issues(self, start=None, limit=None):
        url = self.base_url + 'issues/'
        query = smart_encode(start=start, limit=limit)
        if query: url += '?%s' % query
        return json.loads(self.bb.load_url(url))

    def events(self):
        url = self.base_url + 'events/'
        return json.loads(self.bb.load_url(url))

    def followers(self):
        url = self.base_url + 'followers/'
        return json.loads(self.bb.load_url(url))

    def __repr__(self):
        return '<Repository: %s\'s %s>' % (self.username, self.slug)

class Issue(object):
    def __init__(self, bb, username, slug, number):
        self.bb = bb
        self.username = username
        self.slug = slug
        self.number = number
        self.base_url = api_base + 'repositories/%s/%s/issues/%s/' % (username, slug, number)

    def get(self):
        return json.loads(self.bb.load_url(self.base_url))

    def followers(self):
        url = self.base_url + 'followers/'
        return json.loads(self.bb.load_url(url))

    def __repr__(self):
        return '<Issue #%s on %s\'s %s>' % (self.number, self.username, self.slug)

