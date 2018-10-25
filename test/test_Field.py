from __future__ import print_function
import datetime
import inspect
import os
import unittest

import numpy

import cfdm

class FieldTest(unittest.TestCase):
    def setUp(self):
        self.filename = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'test_file.nc')
        self.contiguous = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       'DSG_timeSeries_contiguous.nc')
        
        f = cfdm.read(self.filename)
        self.assertTrue(len(f)==1, 'f={}'.format(f))
        self.f = f[0]
#        print(self.f)
        self.test_only = []
#        self.test_only = ['test_Field_squeeze']
#        self.test_only = ['test_Field_domain_axes']
#        self.test_only = ['test_Field_axes','test_Field_data_axes']
#        self.test_only = ['test_Field___getitem__']
#        self.test_only = ['test_Field___setitem__']
#        self.test_only = ['test_Field_expand_dims']
#        self.test_only = ['test_Field_field']

    def test_Field___getitem__(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        f = f.squeeze()
        
        d = f.get_array()
        
        g = f[...]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[:, :]
        self.assertTrue((g.get_array() == d).all())
        
        g = f[slice(None), :]
        self.assertTrue((g.get_array()== d).all())
        
        g = f[slice(None), slice(None)]
        self.assertTrue((g.get_array()== d).all())
        
        g = f[slice(None), ...]
        self.assertTrue((g.get_array()== d).all())
        
        g = f[..., slice(None)]
        self.assertTrue((g.get_array()== d).all())
        
        g = f[:, slice(0, f.data.shape[1], 1)]
        self.assertTrue((g.get_array() == d).all())
        
        for indices, shape, multiple_list_indices in (
                [(slice(0, None, 1), slice(0, None)) , (10, 9), False],
                [(slice(3, 7)      , slice(2, 5))    , ( 4, 3), False],
                [(slice(6, 2, -1)  , slice(4, 1, -1)), ( 4, 3), False],
#               [(1                , 3)              , ( 1, 1), False],
#               [(-2               , -4)             , ( 1, 1), False],
#               [(-2               , slice(1, 5))    , ( 1, 4), False],
#               [(slice(5, 1, -2)  , 7)              , ( 2, 1), False],
                [([1, 4, 7]        , slice(1, 5))    , ( 3, 4), False],
                [([1, 4, 7]        , slice(6, 8))    , ( 3, 2), False],
                [(slice(6, 8)      , [1, 4, 7])      , ( 2, 3), False],
                [([0, 3, 8]        , [1, 7, 8])      , ( 3, 3), True],
                [([8, 3, 0]        , [8, 7, 1])      , ( 3, 3), True]
        ):
            g = f[indices]

            if not multiple_list_indices:
                e = d[indices]
            else:
                e = d.copy()
                indices = list(indices)
                for axis, i in enumerate(indices):
                    if isinstance(i, list):
                        e = numpy.take(e, indices=i, axis=axis)
                        indices[axis] = slice(None)
    
                e = e[tuple(indices)]
            #--- End: if
            
            self.assertTrue(g.data.shape == e.data.shape,
                            'Bad shape for {}: {} != {}'.format(
                                indices,
                                g.data.shape,
                                e.data.shape))
            self.assertTrue((g.get_array() == e).all(),
                            'Bad values for {}: {} != {}'.format(indices,
                                                                 g.get_array(),
                                                                 e))
    #--- End: def

#    def test_Field___setitem__(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = self.f.squeeze()
#        
#        f[...] = 0
#        self.assertTrue((f.get_array() == 0).all())
#
#        f[:, :] = 0
#        self.assertTrue((f.get_array() == 0).all())
#
#
#        for indices in [
#                (slice(None)    , slice(None)),
#                (slice(3, 7)    , slice(None)),
#                (slice(None)    , slice(2, 5)),
#                (slice(3, 7)    , slice(2, 5)),
#                (slice(6, 2, -1), slice(4, 1, -1)),
#                (slice(2, 6)    , slice(4, 1, -1)),
#                ([0, 3, 8]      , [1, 7, 8]),
#                ([7, 4, 1]      , slice(6, 8)),
#        ]:
#            f[...] = 0
#            f[indices] = -1
#            array = f[indices].get_array()
#            self.assertTrue((array == -1).all())
#            
#            values, counts = numpy.unique(f.get_array(), return_counts=True)
#            self.assertTrue(counts[0] == array.size)
#    #--- End: def

    def test_Field_auxiliary_coordinates(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        auxiliary_coordinates = f.auxiliary_coordinates()
        
        self.assertTrue(len(auxiliary_coordinates) == 3,
                        'auxiliary_coordinates={}'.format(auxiliary_coordinates))

        for key, value in auxiliary_coordinates.items():
            self.assertTrue(isinstance(value, cfdm.AuxiliaryCoordinate))
    #--- End: def

    def test_Field_cell_measures(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        constructs = f.cell_measures()
                
        self.assertTrue(len(constructs) == 1)

        for key, value in constructs.items():
            self.assertTrue(isinstance(value, cfdm.CellMeasure))
    #--- End: def

    def test_Field_cell_methods(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        constructs = f.cell_methods()
                
        self.assertTrue(len(constructs) == 2)

        for key, value in constructs.items():
            self.assertTrue(isinstance(value, cfdm.CellMethod))
    #--- End: def

    def test_Field_coordinate_references(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        constructs = f.coordinate_references()
                
        self.assertTrue(len(constructs) == 2)

        for key, value in constructs.items():
            self.assertTrue(isinstance(value, cfdm.CoordinateReference))
    #--- End: def

    def test_Field_data_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        ref = f.get_data_axes()
        
        self.assertTrue(f.get_data_axes(None) == ref)

        self.assertTrue(f.del_data_axes() == ref)
        self.assertTrue(f.del_data_axes(None) == None)        
        
        self.assertTrue(f.set_data_axes(ref) == None)
        self.assertTrue(f.get_data_axes() == ref)
    #--- End: def

    def test_Field_dimension_coordinates(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        dimension_coordinates = f.dimension_coordinates()
                
        self.assertTrue(len(dimension_coordinates) == 3)

        for key, value in dimension_coordinates.items():
            self.assertTrue(isinstance(value, cfdm.DimensionCoordinate))
    #--- End: def

    def test_Field_domain_ancillaries(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        constructs = f.domain_ancillaries()
                
        self.assertTrue(len(constructs) == 3)

        for key, value in constructs.items():
            self.assertTrue(isinstance(value, cfdm.DomainAncillary))
    #--- End: def

    def test_Field_domain_axes(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        domain_axes = f.domain_axes()
        
        self.assertTrue(len(domain_axes) == 3)

        for key, value in domain_axes.items():
            self.assertTrue(isinstance(value, cfdm.DomainAxis))

        key = f.set_domain_axis(cfdm.DomainAxis(1))
        self.assertTrue(len(f.domain_axes()) == 4)
      
    #--- End: def

    def test_Field_equals(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        self.assertTrue(f.equals(f, traceback=True))

        g = f.copy()
        self.assertTrue(f.equals(g, traceback=True))

        g = g.squeeze()
        self.assertFalse(f.equals(g))

        h = f.copy()
        h.get_data()[...] = h.get_array()[...] + 1
        self.assertFalse(f.equals(h))
    #--- End: def

    def test_Field_expand_dims(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        
        g = f.copy()

        key = g.set_domain_axis(cfdm.DomainAxis(1))
        h = g.expand_dims(axis=key)
        self.assertTrue(h.data.ndim == f.data.ndim + 1)
        self.assertTrue(h.get_data_axes()[1:] == f.get_data_axes())

        key = g.set_domain_axis(cfdm.DomainAxis(1))
        h = g.expand_dims(position=g.data.ndim, axis=key)
        self.assertTrue(h.data.ndim == f.data.ndim + 1)
        self.assertTrue(h.get_data_axes()[:-1] == f.get_data_axes())
    #--- End: def

    def test_Field_field_ancillaries(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()

        constructs = f.field_ancillaries()
                
        self.assertTrue(len(constructs) == 3)

        for key, value in constructs.items():
            self.assertTrue(isinstance(value, cfdm.FieldAncillary))
    #--- End: def

#    def test_Field_construct_axes(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = self.f.copy()
#
#    #--- End: def

    def test_Field_squeeze(self):
        if self.test_only and inspect.stack()[0][3] not in self.test_only:
            return

        f = self.f.copy()
        g = f.squeeze()
    #--- End: def


#    def test_Field_field(self):
#        if self.test_only and inspect.stack()[0][3] not in self.test_only:
#            return
#
#        f = cfdm.read(self.filename)[0]
#
#        y = f.field('grid_lat')
#        print y
#    #--- End: def

#--- End: class

if __name__ == '__main__':
    print('Run date:', datetime.datetime.now())
    cfdm.environment()
    print('')
    unittest.main(verbosity=2)
