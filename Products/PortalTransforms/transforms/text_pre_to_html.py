from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.utils import RegistryProxy
from zope.interface import implements
from DocumentTemplate.DT_Util import html_quote


class TextPreToHTML:
    """simple transform which wraps raw text into a <pre> tag"""

    implements(ITransform)

    __name__ = "text-pre_to_html"
    inputs = ('text/plain-pre',)
    output = "text/html"

    def __init__(self, name=None):
        if name:
            self.__name__ = name
        self.config = RegistryProxy(self.__name__)

    def name(self):
        return self.__name__

    def __getattr__(self, attr):
        if attr == 'inputs':
            return self.config['inputs']
        if attr == 'output':
            return self.config['output']
        raise AttributeError(attr)

    def convert(self, orig, data, **kwargs):
        data.setData('<pre class="data">%s</pre>' % html_quote(orig))
        return data


def register():
    return TextPreToHTML()
