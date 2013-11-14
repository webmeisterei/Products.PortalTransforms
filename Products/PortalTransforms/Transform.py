from logging import ERROR

from zope.interface import implements
from App.class_init import InitializeClass
from Persistence import PersistentMapping
from Persistence import Persistent
from persistent.list import PersistentList
from AccessControl import ClassSecurityInfo

from Products.CMFCore.permissions import ManagePortal

from Products.PortalTransforms.interfaces import ITransform
from Products.PortalTransforms.utils import TransformException, log
from Products.PortalTransforms.transforms.broken import BrokenTransform
from zope.component import getUtility
from plone.registry.interfaces import IRegistry


def import_from_name(module_name):
    """ import and return a module by its name """
    __traceback_info__ = (module_name, )
    m = __import__(module_name)
    try:
        for sub in module_name.split('.')[1:]:
            m = getattr(m, sub)
    except AttributeError, e:
        raise ImportError(str(e))
    return m


VALIDATORS = {
    'int': int,
    'string': str,
    'list': PersistentList,
    'dict': PersistentMapping,
    }


class Transform(Persistent):
    """A transform is an external method with
    additional configuration information
    """

    implements(ITransform)

    security = ClassSecurityInfo()
    __allow_access_to_unprotected_subobjects__ = 1

    def __init__(self, id, module, transform=None):
        self.id = id
        self.module = module
        # DM 2004-09-09: 'Transform' instances are stored as
        #  part of a module level configuration structure
        #  Therefore, they must not contain persistent objects
        self._tr_init(1, transform)

    def __repr__(self):
        return '<Transform at %s>' % self.id

    def __setstate__(self, state):
        """ __setstate__ is called whenever the instance is loaded
            from the ZODB, like when Zope is restarted.

            We should reload the wrapped transform at this time
        """
        Transform.inheritedAttribute('__setstate__')(self, state)
        self._tr_init()

    def _tr_init(self, set_conf=0, transform=None):
        """ initialize the zope transform by loading the wrapped transform """
        __traceback_info__ = (self.module, )
        if transform is None:
            transform = self._load_transform()
        else:
            self._v_transform = transform
        # check this is a valid transform
        if not hasattr(transform, '__class__'):
            raise TransformException(
                'Invalid transform : transform is not a class')
        if not ITransform.providedBy(transform):
            raise TransformException(
                'Invalid transform : ITransform is not implemented by %s' %
                transform.__class__)
        if not hasattr(transform, 'inputs'):
            raise TransformException(
                'Invalid transform : missing required "inputs" attribute')
        if not hasattr(transform, 'output'):
            raise TransformException(
                'Invalid transform : missing required "output" attribute')

        self.inputs = transform.inputs
        self.output = transform.output
        self.output_encoding = getattr(transform, 'output_encoding', None)
        return transform

    def _load_transform(self):
        try:
            m = import_from_name(self.module)
        except ImportError, err:
            transform = BrokenTransform(self.id, self.module, err)
            msg = ("Cannot register transform %s (ImportError), using "
                   "BrokenTransform: Error\n %s" % (self.id, err))
            self.title = 'BROKEN'
            log(msg, severity=ERROR)
            return transform
        if not hasattr(m, 'register'):
            msg = ("Invalid transform module %s: no register function "
                   "defined" % self.module)
            raise TransformException(msg)
        try:
            transform = m.register()
        except Exception, err:
            transform = BrokenTransform(self.id, self.module, err)
            msg = ("Cannot register transform %s, using BrokenTransform: "
                   "Error\n %s" % (self.id, err))
            self.title = 'BROKEN'
            log(msg, severity=ERROR)
        else:
            self.title = ''
        self._v_transform = transform
        return transform

    security.declarePublic('get_documentation')
    def get_documentation(self):
        """ return transform documentation """
        if not hasattr(self, '_v_transform'):
            self._load_transform()
        return self._v_transform.__doc__

    security.declarePublic('convert')
    def convert(self, *args, **kwargs):
        # return apply the transform and return the result
        if not hasattr(self, '_v_transform'):
            self._load_transform()
        return self._v_transform.convert(*args, **kwargs)

    security.declarePublic('name')
    def name(self):
        """return the name of the transform instance"""
        return self.id

    security.declareProtected(ManagePortal, 'reload')
    def reload(self):
        """ reload the module where the transformation class is defined """
        log('Reloading transform %s' % self.module)
        m = import_from_name(self.module)
        reload(m)
        self._tr_init()

InitializeClass(Transform)
