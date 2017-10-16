import collections

from . import logger
from .utils import is_simple_callable


def get_attribute(instance, attrs):

    for attr in attrs.split('.'):

        try:
            if isinstance(instance, collections.Mapping):
                instance = instance[attr]
            else:
                instance = getattr(instance, attr)
        except AttributeError:
            logger.debug(
                "{} dn't have attribute '{}'. Try: {}".format(
                    repr(instance),
                    attr,
                    ', '.join(
                        a for a in dir(instance)
                        if not a.startswith('__') and
                        (not callable(a) or is_simple_callable(a))
                    )
                ),
            )
            return
        except KeyError:
            return

        if is_simple_callable(instance):
            try:
                instance = instance()
            except:
                logger.debug("error while calling {}".format(repr(instance)))

    return instance
