import datetime
import inspect
import unittest

import cfdm


def _recurse_on_subclasses(klass):
    """Return as a set all subclasses in a classes' subclass hierarchy."""
    return set(klass.__subclasses__()).union(
        [sub for cls in klass.__subclasses__() for sub in
         _recurse_on_subclasses(cls)]
    )


def _get_all_abbrev_subclasses(klass):
    """Return set of all subclasses in class hierarchy, filtering some out.

    Filter out cf.mixin.properties*.Properties* (by means of there not being
    any abbreviated cf.Properties* classes) plus any cfdm classes, since
    this function needs to take cf subclasses from cfdm classes as well.
    """
    return tuple([
        sub for sub in _recurse_on_subclasses(klass) if
        hasattr(cfdm, sub.__name__)
    ])


class DocstringTest(unittest.TestCase):
    def setUp(self):
        self.package = 'cfdm'
        self.repr = ''

        self.subclasses_of_Container = tuple(
            set(_get_all_abbrev_subclasses(
                cfdm.mixin.container.Container)).union(
                set(_get_all_abbrev_subclasses(
                    cfdm.core.abstract.container.Container)),
                set(_get_all_abbrev_subclasses(
                    cfdm.data.abstract.array.Array)),
                [   # other key classes not in subclass heirarchy above
                    cfdm.data.NumpyArray
                ]
            )
        )

        self.subclasses_of_Properties = _get_all_abbrev_subclasses(
            cfdm.mixin.properties.Properties)

        self.subclasses_of_PropertiesData = _get_all_abbrev_subclasses(
            cfdm.mixin.propertiesdata.PropertiesData)

        self.subclasses_of_PropertiesDataBounds = _get_all_abbrev_subclasses(
            cfdm.mixin.propertiesdatabounds.PropertiesDataBounds)

    def test_docstring(self):
        # Test that all {{ occurences have been substituted
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                for name in dir(x):
                    f = getattr(klass, name, None)

                    if f is None or not hasattr(f, '__doc__'):
                        continue

                    if name.startswith('__') and not inspect.isfunction(f):
                        continue

                    self.assertIsNotNone(
                        f.__doc__,
                        "\n\nCLASS: {}\n"
                        "METHOD NAME: {}\n"
                        "METHOD: {}\n__doc__: {}".format(
                            klass, name, f, f.__doc__))

                    self.assertNotIn(
                        '{{', f.__doc__,
                        "\n\nCLASS: {}\n"
                        "METHOD NAME: {}\n"
                        "METHOD: {}".format(
                            klass, name, f))

    def test_docstring_package(self):
        string = '>>> f = {}.'.format(self.package)
        for klass in self.subclasses_of_Container:
            for x in (klass, klass()):
                self.assertIn(string, x._has_component.__doc__, klass)

        string = '>>> f = {}.'.format(self.package)
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.clear_properties.__doc__, klass)

    def test_docstring_class(self):
        for klass in self.subclasses_of_Properties:
            string = '>>> f = {}.{}'.format(self.package, klass.__name__)
            for x in (klass, klass()):
                self.assertIn(
                    string, x.clear_properties.__doc__,
                    "\n\nCLASS: {}\n"
                    "METHOD NAME: {}\n"
                    "METHOD: {}".format(
                        klass, 'clear_properties', x.clear_properties))

        for klass in self.subclasses_of_Container:
            string = klass.__name__
            for x in (klass, klass()):
                self.assertIn(string, x.copy.__doc__, klass)

        for klass in self.subclasses_of_PropertiesDataBounds:
            string = '{}'.format(klass.__name__)
            for x in (klass, klass()):
                self.assertIn(
                    string, x.insert_dimension.__doc__,
                    "\n\nCLASS: {}\n"
                    "METHOD NAME: {}\n"
                    "METHOD: {}".format(
                        klass, klass.__name__, 'insert_dimension'))

    def test_docstring_repr(self):
        string = '<{}Data'.format(self.repr)
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertIn(string, x.has_data.__doc__, klass)

    def test_docstring_default(self):
        string = 'Return the value of the *default* parameter'
        for klass in self.subclasses_of_Properties:
            for x in (klass, klass()):
                self.assertIn(string, x.del_property.__doc__, klass)

    def test_docstring_staticmethod(self):
        string = 'Return the value of the *default* parameter'
        for klass in self.subclasses_of_PropertiesData:
            x = klass
            self.assertEqual(
                x._test_docstring_substitution_staticmethod(1, 2),
                (1, 2)
            )

    def test_docstring_classmethod(self):
        string = 'Return the value of the *default* parameter'
        for klass in self.subclasses_of_PropertiesData:
            for x in (klass, klass()):
                self.assertEqual(
                    x._test_docstring_substitution_classmethod(1, 2),
                    (1, 2)
                )

    def test_docstring_docstring_substitutions(self):
        for klass in self.subclasses_of_Container:
            for x in (klass,):
                d = x._docstring_substitutions(klass)
                self.assertIsInstance(d, dict)
                self.assertIn('{{repr}}', d)

# --- End: class


if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
