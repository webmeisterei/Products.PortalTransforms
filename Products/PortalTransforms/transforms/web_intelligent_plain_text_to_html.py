from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.utils import RegistryProxy
from zope.interface import implements
from plone.intelligenttext.transforms import \
    convertWebIntelligentPlainTextToHtml


class WebIntelligentPlainTextToHtml:
    """Transform which replaces urls and email into hyperlinks"""

    implements(ITransform)

    __name__ = "web_intelligent_plain_text_to_html"
    output = "text/html"
    inputs = ('text/x-web-intelligent',)
    tab_width = 4

    def __init__(self, name=None, inputs=('text/x-web-intelligent',),
                 tab_width=4):
        if name:
            self.__name__ = name
        self.inputs = inputs
        self.tab_width = tab_width
        self.config = RegistryProxy(self.__name__)

    def name(self):
        return self.__name__

    def convert(self, orig, data, **kwargs):
        text = convertWebIntelligentPlainTextToHtml(
            orig, tab_width=self.tab_width)
        data.setData(text)
        return data


def register():
    return WebIntelligentPlainTextToHtml()
