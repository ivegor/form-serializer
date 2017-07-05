import os
from functools import wraps

from . import logger
from .utlis import NearestClass
from .base import BaseFieldSerializer, BaseFieldSetSerializer, BaseFormSerializer


class SerializeError(AttributeError):
    pass


class FormSerializer(BaseFormSerializer):
    def __init__(self, form):
        self._form = form

    def serialize(self):
        response = {}
        for f in self._fields:
            response[f] = (getattr(self, f).serialize(self._form, f))
        return response


class SerializerFieldByAttr(BaseFieldSerializer):
    def __init__(self, field_name=None):
        self._field_name = field_name

    def serialize(self, obj, default_field_name):
        path_name = self._field_name or default_field_name

        target_attr = obj
        for attr in path_name.split('.'):
            try:
                target_attr = getattr(target_attr, attr)
            except AttributeError:
                if os.environ.get('DEBUG'):
                    logger.debug(
                        "{} dn't have attribute '{}'. Try: {}".format(
                            repr(target_attr),
                            attr,
                            ', '.join(dir(target_attr))
                        ),
                    )
                return

        if callable(target_attr):
            try:
                target_attr = target_attr()
            except Exception as e:
                if os.environ.get('DEBUG'):
                    logger.debug(e)
                return
        return target_attr


class SerializerFieldMethod(BaseFieldSerializer):
    def __get__(self, instance, owner):
        self._instance = instance

    def serialize(self, obj, field_name):
        method_name = 'get_' + field_name
        try:
            return getattr(self._instance, method_name)(obj)
        except AttributeError:
            raise SerializeError('Method must be called is {}. And take one arg.'.format(method_name))


class SerializerFieldSet(BaseFieldSetSerializer):
    def __init__(self, field_name=None, as_list=True):
        self._field_name = field_name
        if as_list:
            self._container = []
            self._add_to_container = self._add_to_list
        else:
            self._container = {}
            self._add_to_container = self._add_to_dict

    def serialize(self, obj, default_field_name):
        field_set_obj = getattr(obj, self._field_name or default_field_name)

        for k, v in field_set_obj.items():
            field_obj = {}
            serializer = self._get_serializer(v.__class__)

            for f in serializer._fields:
                field_obj[f] = (getattr(serializer, f).serialize(v, f))
            self._add_to_container(k, field_obj)
        return self._container

    def _add_to_list(self, key, value):
        self._container.append(value)

    def _add_to_dict(self, key, value):
        self._container[key] = value

    def _get_serializer(self, model_class):
        try:
            return getattr(self, '_special_serializers')[model_class](self._field_name)
        except (AttributeError, KeyError):
            return self


class specializer:
    def __init__(self, model_class, default_serializer=None):
        self.model_class = model_class
        self.default_serializer = default_serializer

    def __call__(self, cl):
        cl._model = self.model_class

        ds = self.default_serializer or [c for c in cl.__bases__ if issubclass(c, BaseFieldSetSerializer)][0]
        ds._special_serializers = getattr(ds, '_special_serializers', NearestClass())
        ds._special_serializers[cl._model] = cl

        @wraps(cl)
        def wrapper(*args, **kwargs):
            return cl(*args, **kwargs)
        return wrapper
