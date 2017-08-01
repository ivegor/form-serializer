import os
from functools import wraps

from . import logger
from .utils import NearestClass, method_dispatch, Empty
from .base import BaseFieldSerializer, BaseFieldSetSerializer, BaseFormSerializer


class SerializeError(AttributeError):
    pass


class FormSerializer(BaseFormSerializer):
    def __init__(self, form):
        self._form = form

    def serialize(self):
        response = {}
        for name, field in self._fields.items():
            response[name] = field.serialize(self._form, name)
        return response


class SerializerFieldByAttr(BaseFieldSerializer):
    def __init__(self, field_name=None):
        self.field_name = field_name

    def serialize(self, obj, field_name, *args, **kwargs):
        path_name = self.field_name or field_name

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
        self.instance = instance
        return self

    def serialize(self, obj, field_name, *args, **kwargs):
        method_name = 'get_' + field_name
        try:
            return getattr(self.instance, method_name)(obj)
        except AttributeError:
            raise SerializeError('Method must be called is {}. And take one arg.'.format(method_name))


class SerializerFieldSet(BaseFieldSetSerializer):
    def __init__(self, field_name=None, container_type=list, skip_empty=False):
        self.field_name = field_name
        self.container_type = container_type
        self.skip_empty = skip_empty
        self.empty = Empty

    def serialize(self, obj, field_name, *args, **kwargs):
        field_set_obj = getattr(obj, self.field_name or field_name)
        container = self.container_type()

        for sub_field_name, sub_field_obj in field_set_obj.items():
            serialized_field_obj = self.create_obj_for_container(obj=sub_field_obj,
                                                                 container_name=sub_field_name,
                                                                 *args, **kwargs)
            if not(self.skip_empty and self.empty(serialized_field_obj)):
                self.add_to_container(container, sub_field_name, serialized_field_obj)
        return container

    def create_obj_for_container(self, obj, container_type=dict, *args, **kwargs):
        serializer = self.get_serializer(obj.__class__)
        container = container_type()

        for name, field in serializer._fields.items():
            serialized_field_obj = field.serialize(obj=obj, field_name=name, *args, **kwargs)
            self.add_to_container(container, name, serialized_field_obj)
        return container

    @method_dispatch
    def add_to_container(self, container, field_name, field_obj):
        raise SerializeError('Bad container type')

    @add_to_container.register(list)
    def _(self, container, key, value):
        container.append(value)

    @add_to_container.register(dict)
    def _(self, container, key, value):
        container[key] = value

    def get_serializer(self, model_class):
        try:
            return getattr(self, '_special_serializers')[model_class](self.field_name)
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
