from functools import wraps
from typing import Optional, Type

from .base import BaseFieldSerializer, BaseFieldSetSerializer, BaseFormSerializer
from .help_functions import get_attribute
from .utils import NearestClass, method_dispatch, Empty


class SerializeError(AttributeError):
    pass


class FormSerializer(BaseFormSerializer):
    def __init__(self, form):
        self._form = form

    def serialize(self):
        response = {}
        for name, field in self._fields.items():
            response[name] = field.serialize(obj=self._form, field_name=name, parent=self)
        return response


class SerializerFieldByAttr(BaseFieldSerializer):
    def __init__(self, field_name: Optional[str]=None):
        self.field_name = field_name

    def serialize(self, obj, field_name, *args, **kwargs):
        path_name = self.field_name or field_name
        return get_attribute(obj, path_name)


class SerializerFieldMethod(BaseFieldSerializer):

    def __init__(self, method_name: Optional[str]=None):
        self.method_name = method_name

    def serialize(self, obj, field_name, *args, **kwargs):
        method_name = self.method_name or 'get_' + field_name
        try:
            return getattr(kwargs['parent'], method_name)(obj, field_name, *args, **kwargs)
        except AttributeError:
            raise SerializeError('Method must be called is "{}".'.format(method_name))


class SerializerFieldSet(BaseFieldSetSerializer):
    def __init__(self, field_name: Optional[str]=None, container_type: Type=list, skip_empty: bool=False):
        self.field_name = field_name
        self.container_type = container_type
        self.skip_empty = skip_empty
        self.empty = Empty

    def serialize(self, obj, field_name, *args, **kwargs):
        field_set_obj = get_attribute(obj, self.field_name or field_name)
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
            kwargs['parent'] = serializer
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
    def __init__(self, model_class: type, default_serializer: Type[SerializerFieldSet]=None):
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
