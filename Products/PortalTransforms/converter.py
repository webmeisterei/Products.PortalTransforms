
# convert the current Transform configurations to registry.xml
# XXX: remove this script once this changeset is merged


from lxml.builder import E
from lxml import etree
from Products.PortalTransforms.transforms import transforms


type_map = dict(
    string='plone.registry.field.ASCIILine',
    int='plone.registry.field.Int',
    list='plone.registry.field.List',
    dict='plone.registry.field.Dict',
)

field_map = dict(
    valid_tags=('ASCIILine', 'Bool')
)

if __name__ == '__main__':
    xml = E.registry()
    records = []
    for transform in transforms:
        name = transform.__name__
        if not hasattr(transform, 'config'):
            continue
        if not hasattr(transform, 'config_metadata'):
            continue
        for fieldid, value in transform.config.items():
            metadata = transform.config_metadata.get(fieldid)
            if not metadata:
                continue
            fieldtype = metadata[0]
            fieldlabel = metadata[1]
            fielddesc = metadata[2]
            fieldvals = transform.config.get(fieldid)
            VALUES = []
            if fieldtype in ('dict'):
                types = field_map.get(fieldid)
                if not types:
                    types = ('ASCIILine', 'ASCIILine')
                FIELD = E.field(
                    dict(type=type_map.get(fieldtype)),
                    E.title(fieldlabel),
                    E.key_type('plone.registry.field.%s' % types[0]),
                    E.value_type('plone.registry.field.%s' % types[1]),
                )
                keys = fieldvals.keys()
                keys.sort()
                for key in keys:
                    value = fieldvals.get(key)
                    VALUES.append(E.element(str(value), {'key': key}))
                VALUES = tuple(VALUES)
                records.append(E.record(
                    dict(name='Products.PortalTransforms.%s.%s' % (
                        name, fieldid)),
                    FIELD, E.value(*VALUES)))
            elif fieldtype in ('int'):
                records.append(E.record(
                    dict(name='Products.PortalTransforms.%s.%s' % (
                        name, fieldid)),
                    E.field(
                        dict(type=type_map.get(fieldtype)),
                        E.title(fieldlabel),
                    ),
                    E.value(str(fieldvals))))
            elif fieldtype in ('list'):
                types = field_map.get(fieldid)
                if not types:
                    types = ('ASCIILine', 'ASCIILine')
                FIELD = E.field(
                    dict(type=type_map.get(fieldtype)),
                    E.title(fieldlabel),
                    E.value_type('plone.registry.field.%s' % types[1]),
                )
                for val in fieldvals:
                    VALUES.append(E.element(str(val)))
                VALUES = tuple(VALUES)
                records.append(E.record(
                    dict(name='Products.PortalTransforms.%s.%s' % (
                        name, fieldid)),
                    FIELD, E.value(*VALUES)))
            elif fieldtype in ('string'):
                records.append(E.record(
                    dict(name='Products.PortalTransforms.%s.%s' % (
                        name, fieldid)),
                    E.field(
                        dict(type=type_map.get(fieldtype)),
                        E.title(fieldlabel),
                    ),
                    E.value(str(fieldvals))))

    records = tuple(records)
    registry = E.registry(*records)

    print etree.tostring(registry, pretty_print=True)
