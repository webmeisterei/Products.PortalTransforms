from Products.PortalTransforms.utils import RegistryProxy
from Products.PortalTransforms.interfaces import ITransform
from zope.interface import implements
from Products.CMFDefault.utils import bodyfinder


class HTMLBody:
    """Simple transform which extracts the content of the body tag"""

    implements(ITransform)

    __name__ = "html_body"

    inputs = ('text/html',)
    output = "text/html"

    def __init__(self, name=None):
        if name:
            self.__name__ = name
        self.config = RegistryProxy(self.__name__)

    def name(self):
        return self.__name__

    def convert(self, orig, data, **kwargs):
        body = bodyfinder(orig)
        data.setData(body)
        return data


def register():
    return HTMLBody()
