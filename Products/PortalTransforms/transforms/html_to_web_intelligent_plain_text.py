from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.utils import RegistryProxy
from zope.interface import implements
from plone.intelligenttext.transforms import \
    convertHtmlToWebIntelligentPlainText


class HtmlToWebIntelligentPlainText:
    """Transform which replaces urls and email into hyperlinks"""

    implements(ITransform)

    __name__ = "html_to_web_intelligent_plain_text"
    output = "text/x-web-intelligent"
    inputs = ('text/html',)
    tab_width = 4

    def __init__(self, name=None, inputs=('text/html',), tab_width=4):
        if name:
            self.__name__ = name
        self.inputs = inputs
        self.tab_width = tab_width
        self.config = RegistryProxy(self.__name__)

    def name(self):
        return self.__name__

    def convert(self, orig, data, **kwargs):
        text = convertHtmlToWebIntelligentPlainText(orig)
        data.setData(text)
        return data


def register():
    return HtmlToWebIntelligentPlainText()
