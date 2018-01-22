import unittest

from form_serializer.base import BaseFormSerializer
from form_serializer.components import SerializerFieldByAttr, SerializerFieldMethod, SerializerFieldSet, SerializeError, \
    FormSerializer, specialize


class TestMetaClassFields(unittest.TestCase):

    def setUp(self):
        self.field_by_attr_1 = SerializerFieldByAttr()
        self.field_by_attr_2 = SerializerFieldByAttr()
        self.field_method_1 = SerializerFieldMethod()
        self.field_method_2 = SerializerFieldMethod()
        self.field_set_1 = SerializerFieldSet()
        self.field_set_2 = SerializerFieldSet()
        self.fake_field_1 = None
        self.fake_field_2 = {}
        self.fake_field_3 = []
        self.right_fields = (
            self.field_by_attr_1,
            self.field_by_attr_2,
            self.field_method_1,
            self.field_method_2,
            self.field_set_1,
            self.field_set_2
        )
        self.fake_fields = (
            self.fake_field_1,
            self.fake_field_2,
            self.fake_field_3
        )

    def test_all_positive(self):
        fields = {'f_%i' % i: v for i, v in enumerate(self.right_fields)}
        form = type('test_form', (BaseFormSerializer,), fields)
        self.assertSetEqual(set(form._fields.values()), set(self.right_fields))

    def test_all_negative(self):
        fields = {'f_%i' % i: v for i, v in enumerate(self.fake_fields)}
        form = type('test_form', (BaseFormSerializer,), fields)
        self.assertSequenceEqual(form._fields.values(), [])

    def test_mixed(self):
        fields = {'f_%i' % i: v for i, v in enumerate(self.right_fields+self.fake_fields)}
        form = type('test_form', (BaseFormSerializer,), fields)
        self.assertSequenceEqual(set(form._fields.values()), set(self.right_fields))

    def test_inheritance(self):
        fields_base = {
            'f_1': self.field_by_attr_1,
            'f_2': self.field_method_1
        }
        form_base = type('test_form', (BaseFormSerializer,), fields_base.copy())
        fields_inheritance = {
            'f_2': self.field_method_2,
            'f_3': self.field_set_1
        }
        form_inheritance = type('test_form', (form_base,), fields_inheritance)
        self.assertSetEqual(set(form_base._fields.values()), set(fields_base.values()))
        self.assertSetEqual(set(form_inheritance._fields.values()),
                            {self.field_by_attr_1, self.field_method_2, self.field_set_1})


class TestForm(unittest.TestCase):
    def setUp(self):
        form = type('test_form', (), {'test_field_1': 1, 'test_field_2': 2})
        self.form = form

    def test_serialize(self):
        serializer_empty_form = FormSerializer(self.form)
        self.assertEqual(serializer_empty_form.serialize(), {})

        serialize_right_form = type(
            'test_serializer_form',
            (FormSerializer,),
            {'test_field_1': SerializerFieldByAttr(), 'test_field_2': SerializerFieldByAttr()}
        )(self.form)
        self.assertEqual(serialize_right_form.serialize(), {'test_field_1': 1, 'test_field_2': 2})


class TestFieldByAttr(unittest.TestCase):
    def setUp(self):
        sub_obj = type('test_sub_obj', (), {'sub_field_3': 3})
        self.obj = type('test_obj', (), {'field_1': 1, 'field_2': 2, 'field_3': sub_obj})

    def test_with_name(self):
        serializer_1 = SerializerFieldByAttr('field_1')
        self.assertEqual(serializer_1.serialize(self.obj, 'empty'), 1)
        self.assertEqual(serializer_1.serialize(self.obj, 'field_1'), 1)
        self.assertEqual(serializer_1.serialize(self.obj, 'field_2'), 1)

        serializer_2 = SerializerFieldByAttr('field_2')
        self.assertEqual(serializer_2.serialize(self.obj, 'empty'), 2)
        self.assertEqual(serializer_2.serialize(self.obj, 'field_1'), 2)
        self.assertEqual(serializer_2.serialize(self.obj, 'field_2'), 2)

        serializer_3 = SerializerFieldByAttr('field_3.sub_field_3')
        self.assertEqual(serializer_3.serialize(self.obj, 'empty'), 3)
        self.assertEqual(serializer_3.serialize(self.obj, 'field_1'), 3)
        self.assertEqual(serializer_3.serialize(self.obj, 'field_2'), 3)

        serializer_4 = SerializerFieldByAttr('field_4')
        self.assertEqual(serializer_4.serialize(self.obj, 'empty'), None)
        self.assertEqual(serializer_4.serialize(self.obj, 'field_1'), None)
        self.assertEqual(serializer_4.serialize(self.obj, 'field_2'), None)

        serializer_5 = SerializerFieldByAttr('field_4.sub_5')
        self.assertEqual(serializer_5.serialize(self.obj, 'empty'), None)
        self.assertEqual(serializer_5.serialize(self.obj, 'field_1'), None)
        self.assertEqual(serializer_5.serialize(self.obj, 'field_2'), None)

    def test_wo_name(self):
        serializer = SerializerFieldByAttr()
        self.assertEqual(serializer.serialize(self.obj, 'empty'), None)
        self.assertEqual(serializer.serialize(self.obj, 'field_1'), 1)
        self.assertEqual(serializer.serialize(self.obj, 'field_2'), 2)
        self.assertEqual(serializer.serialize(self.obj, 'field_3.sub_field_3'), 3)


class TestFieldMethod(unittest.TestCase):
    def setUp(self):
        self.obj = type('test_obj', (), {'field_1': 1})
        method_1 = lambda o, f, *args, **kwargs: o.field_1
        method_2 = lambda o, f, *args, **kwargs: f
        self.parent = type('test_parent', (), {'get_method_1': method_1, 'get_method_2': method_2})

    def test_with_name(self):
        serializer = SerializerFieldMethod()
        self.assertEqual(serializer.serialize(self.obj, 'method_1', parent=self.parent), 1)
        self.assertEqual(serializer.serialize(self.obj, 'method_2', parent=self.parent), 'method_2')
        with self.assertRaises(SerializeError) as er:
            serializer.serialize(self.obj, 'method_3', parent=self.parent)
        self.assertTrue('Method must be called is "get_method_3"' in str(er.exception))

    def test_wo_name(self):
        serializer_1 = SerializerFieldMethod('get_method_1')
        self.assertEqual(serializer_1.serialize(self.obj, 'method_1', parent=self.parent), 1)
        self.assertEqual(serializer_1.serialize(self.obj, 'empty', parent=self.parent), 1)

        serializer_2 = SerializerFieldMethod('get_method_2')
        self.assertEqual(serializer_2.serialize(self.obj, 'method_1', parent=self.parent), 'method_1')
        self.assertEqual(serializer_2.serialize(self.obj, 'empty', parent=self.parent), 'empty')


class TestFieldSet(unittest.TestCase):
    def setUp(self):
        class TField:
            field_1 = 1

        class TObj:
            field_set = {'f_1': TField()}

        class TFieldSet(SerializerFieldSet):
            field_1 = SerializerFieldByAttr()

        self.obj = TObj()
        self.field_set = TFieldSet

    def test_serialize(self):
        serializer = self.field_set()
        self.assertListEqual(serializer.serialize(self.obj, 'field_set'), [{'field_1': 1}])

        serializer = self.field_set('field_set')
        self.assertListEqual(serializer.serialize(self.obj, 'field_set'), [{'field_1': 1}])

    def test_container_serialize(self):
        serializer = self.field_set(container_type=list)
        self.assertListEqual(serializer.serialize(self.obj, 'field_set'), [{'field_1': 1}])

        serializer = self.field_set(container_type=dict)
        self.assertDictEqual(serializer.serialize(self.obj, 'field_set'), {'f_1': {'field_1': 1}})

        serializer = self.field_set(container_type=tuple)
        with self.assertRaises(SerializeError) as er:
            serializer.serialize(self.obj, 'field_set')
        self.assertTrue('Bad container type' == str(er.exception))


class TestFieldSetSpecializer(unittest.TestCase):
    def setUp(self):
        class TField1:
            field_1 = 1
            field_2 = 2

        class TField2:
            field_1 = 'field'
            field_3 = 3

        class TObj:
            field_set = {'f_1': TField1(), 'f_2': TField2()}

        class DefaultFieldSet(SerializerFieldSet):
            field_1 = SerializerFieldByAttr()
            field_2 = SerializerFieldByAttr()

        @specialize(TField2)
        class CustomFieldSet(DefaultFieldSet):
            field_1 = SerializerFieldByAttr()
            field_3 = SerializerFieldByAttr()

        self.obj = TObj()
        self.field_set = DefaultFieldSet

    def test_serialize_with_empty(self):
        serializer = self.field_set(container_type=dict)
        self.assertDictEqual(
            serializer.serialize(self.obj, 'field_set'),
            {
                'f_1': {'field_1': 1, 'field_2': 2},
                'f_2': {'field_1': 'field', 'field_2': None, 'field_3': 3}
            }
        )

    def test_serialize_wo_empty(self):
        serializer = self.field_set(container_type=dict, skip_empty=True)
        self.assertDictEqual(
            serializer.serialize(self.obj, 'field_set'),
            {
                'f_1': {'field_1': 1, 'field_2': 2},
                'f_2': {'field_1': 'field', 'field_3': 3}
            }
        )


if __name__ == '__main_':
    unittest.main()
