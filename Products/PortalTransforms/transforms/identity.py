"""
A simple identity transform
"""

from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.utils import RegistryProxy
from zope.interface import implements


class IdentityTransform:
    """ Identity transform

    return content unchanged.
    """
    implements(ITransform)

    __name__ = "rest_to_text"
    inputs = ('text/x-rst',)
    output = 'text/plain'

    def __init__(self, name=None, **kwargs):
        if name:
            self.__name__ = name
        self.config = RegistryProxy(self.__name__)

    def __getattr__(self, attr):
        if attr == 'inputs':
            return self.config['inputs']
        if attr == 'output':
            return self.config['output']
        raise AttributeError(attr)

    def name(self):
        return self.__name__

    def convert(self, data, cache, **kwargs):
        cache.setData(data)
        return cache


def register():
    return IdentityTransform()
