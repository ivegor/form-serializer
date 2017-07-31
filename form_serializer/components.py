import os
from functools import wraps

from . import logger
from .utils import NearestClass
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

    def serialize(self, obj, field_name, *args, **kwargs):
        path_name = self._field_name or field_name

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
        return self

    def serialize(self, obj, field_name, *args, **kwargs):
        method_name = 'get_' + field_name
        try:
            return getattr(self._instance, method_name)(obj)
        except AttributeError:
            raise SerializeError('Method must be called is {}. And take one arg.'.format(method_name))


class SerializerFieldSet(BaseFieldSetSerializer):
    def __init__(self, field_name=None, container_type=list):
        self._field_name = field_name
        self._container_type = container_type

    def serialize(self, obj, field_name, *args, **kwargs):
        field_set_obj = getattr(obj, self._field_name or field_name)
        container = self._container_type()

        for sub_field_name, sub_field_obj in field_set_obj.items():
            kwargs['sub_field_name'] = sub_field_name
            serialized_field_obj = self._create_obj_for_container(sub_field_obj, *args, **kwargs)
            self._add_to_container(container, sub_field_name, serialized_field_obj)
        return container

    def _create_obj_for_container(self, obj, *args, **kwargs):
        field_obj = {}
        serializer = self._get_serializer(obj.__class__)

        for f in serializer._fields:
            field_obj[f] = (getattr(serializer, f).serialize(obj=obj, field_name=f, *args, **kwargs))
        return field_obj

    def _add_to_container(self, container, field_name, field_obj):
        # some monkey patching
        if self._container_type is list:
            self._add_to_container = self._add_to_list
        elif self._container_type is dict:
            self._add_to_container = self._add_to_dict
        else:
            raise SerializeError('Invalid container type')

        self._add_to_container(container, field_name, field_obj)

    def _add_to_list(self, container, key, value):
        container.append(value)

    def _add_to_dict(self, container, key, value):
        container[key] = value

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
