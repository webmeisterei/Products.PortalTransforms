from sgmllib import SGMLParser, SGMLParseError
import re
from cgi import escape

from Products.PortalTransforms.interfaces import ITransform
from zope.interface import implements
from Products.CMFDefault.utils import bodyfinder
from Products.CMFDefault.utils import IllegalHTML
from Products.PortalTransforms.utils import safeToInt, html5entities
from Products.PortalTransforms.utils import RegistryProxy

msg_pat = """
<div class="system-message">
<p class="system-message-title">System message: %s</p>
%s</d>
"""

CSS_COMMENT = re.compile(r'/\*.*\*/')

VALID_TAGS = {}


def hasScript(s):
    """Dig out evil Java/VB script inside an HTML attribute.

    >>> hasScript('data:text/html;base64,PHNjcmlwdD5hbGVydCgidGVzdCIpOzwvc2NyaXB0Pg==')
    True
    >>> hasScript('script:evil(1);')
    True
    >>> hasScript('expression:evil(1);')
    True
    >>> hasScript('expression/**/:evil(1);')
    True
    >>> hasScript('http://foo.com/ExpressionOfInterest.doc')
    False
    """
    s = decode_htmlentities(s)
    s = s.replace('\x00', '')
    s = CSS_COMMENT.sub('', s)
    s = ''.join(s.split()).lower()
    for t in ('script:', 'expression:', 'expression(', 'data:'):
        if t in s:
            return True
    return False


CHR_RE = re.compile(r'\\(\d+)')


def unescape_chr(matchobj):
    try:
        return chr(int(matchobj.group(1), 16))
    except ValueError:
        return matchobj.group(0)


def decode_charref(s):
    s = s.group(1)
    try:
        if s[0] in ['x', 'X']:
            c = int(s[1:], 16)
        else:
            c = int(s)
        c = unichr(c)
        if isinstance(s, str):
            c = c.encode('utf8')
        return c
    except ValueError:
        return '&#' + s + ';'


def decode_entityref(s):
    s = s.group(1)
    try:
        c = html5entities[s + ';']
    except KeyError:
        try:
            c = html5entities[s]
        except KeyError:
            # strip unrecognized entities
            c = u''
    if isinstance(s, str):
        c = c.encode('utf8')
    return c


CHARREF_RE = re.compile(r"&(?:amp;)?#([xX]?[0-9a-fA-F]+);?")
ENTITYREF_RE = re.compile(r"&(\w{1,32});?")


def decode_htmlentities(s):
    # Decode HTML5 entities (numeric or named).
    s = CHR_RE.sub(unescape_chr, s)
    if '&' not in s:
        return s
    s = CHARREF_RE.sub(decode_charref, s)
    return ENTITYREF_RE.sub(decode_entityref, s)


class StrippingParser(SGMLParser):
    """Pass only allowed tags;  raise exception for known-bad.

    Copied from Products.CMFDefault.utils
    Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved.
    """

    # This replaces SGMLParser.entitydefs
    entitydefs = html5entities

    def __init__(self, valid, nasty, remove_javascript, raise_error):
        SGMLParser.__init__(self)
        self.result = []
        self.valid = valid
        self.nasty = nasty
        self.remove_javascript = remove_javascript
        self.raise_error = raise_error
        self.suppress = False

    def handle_data(self, data):
        if self.suppress:
            return
        if data:
            self.result.append(escape(data))

    def handle_charref(self, name):
        if self.suppress:
            return
        self.result.append(self.convert_charref(name))

    def handle_comment(self, comment):
        pass

    def handle_decl(self, data):
        pass

    def handle_entityref(self, name):
        if self.suppress:
            return
        self.result.append(self.convert_entityref(name))

    def convert_entityref(self, name):
        if name + ';' in self.entitydefs:
            x = ';'
        elif name in self.entitydefs:
            x = ''
        else:
            x = ';'
        return '&%s%s' % (name, x)

    def convert_charref(self, name):
        return '&#%s;' % name

    def unknown_starttag(self, tag, attrs):
        """ Delete all tags except for legal ones.
        """
        if self.suppress:
            return

        if tag in self.valid:
            self.result.append('<' + tag)

            remove_script = getattr(self, 'remove_javascript', True)

            for k, v in attrs:
                if remove_script and k.strip().lower().startswith('on'):
                    if not self.raise_error:
                        continue
                    else:
                        raise IllegalHTML('Script event "%s" not allowed.' % k)
                elif remove_script and hasScript(v):
                    if not self.raise_error:
                        continue
                    else:
                        raise IllegalHTML('Script URI "%s" not allowed.' % v)
                else:
                    self.result.append(' %s="%s"' % (k, v))

            #UNUSED endTag = '</%s>' % tag
            if safeToInt(self.valid.get(tag)):
                self.result.append('>')
            else:
                self.result.append(' />')
        elif tag in self.nasty:
            self.suppress = True
            if self.raise_error:
                raise IllegalHTML('Dynamic tag "%s" not allowed.' % tag)
        else:
            # omit tag
            pass

    def unknown_endtag(self, tag):
        if tag in self.nasty and not tag in self.valid:
            self.suppress = False
        if self.suppress:
            return
        if safeToInt(self.valid.get(tag)):
            self.result.append('</%s>' % tag)

    def parse_declaration(self, i):
        """Fix handling of CDATA sections. Code borrowed from BeautifulSoup.
        """
        j = None
        if self.rawdata[i:i + 9] == '<![CDATA[':
            k = self.rawdata.find(']]>', i)
            if k == -1:
                k = len(self.rawdata)
            j = k + 3
        else:
            try:
                j = SGMLParser.parse_declaration(self, i)
            except SGMLParseError:
                j = len(self.rawdata)
        return j

    def getResult(self):
        return ''.join(self.result)


def scrubHTML(html, valid, nasty,
              remove_javascript=True, raise_error=True):

    """ Strip illegal HTML tags from string text.
    """
    parser = StrippingParser(valid=valid, nasty=nasty,
                             remove_javascript=remove_javascript,
                             raise_error=raise_error)
    parser.feed(html)
    parser.close()
    return parser.getResult()


class SafeHTML:
    """Simple transform which uses CMFDefault functions to
    clean potentially bad tags.

    Tags must explicit be allowed in valid_tags to pass. Only
    the tags themself are removed, not their contents. If tags
    are removed and in nasty_tags, they are removed with
    all of their contents.

    Objects will not be transformed again with changed settings.
    You need to clear the cache by e.g.
    1.) restarting your zope or
    2.) empty the zodb-cache via ZMI -> Control_Panel
        -> Database Management -> main || other_used_database
        -> Flush Cache.
    """

    implements(ITransform)

    __name__ = "safe_html"
    inputs = ('text/html', )
    output = "text/x-html-safe"

    def __init__(self, name=None, **kwargs):
        if name:
            self.__name__ = name
        self.config = RegistryProxy(self.__name__)

    def name(self):
        return self.__name__

    def convert(self, orig, data, **kwargs):
        # if we have a config that we don't want to delete
        # we need a disable option
        if self.config.get('disable_transform'):
            data.setData(orig)
            return data

        for repeat in range(2):
            try:
                safe = scrubHTML(
                    bodyfinder(orig),
                    valid=self.config.get('valid_tags', {}),
                    nasty=self.config.get('nasty_tags', {}),
                    remove_javascript=self.config.get(
                        'remove_javascript', True),
                    raise_error=False)
            except IllegalHTML, inst:
                data.setData(msg_pat % ("Error", str(inst)))
                break
            else:
                data.setData(safe)
                orig = safe
        return data


def register():
    return SafeHTML()
