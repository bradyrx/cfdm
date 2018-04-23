import copy
import re
import os
import struct
import sys

import numpy
import netCDF4

from ....functions import abspath, flat

from .. import IOWrite

class NetCDFWrite(IOWrite):
    '''
    '''

    def _check_name(self, base, dimsize=None):
        '''
    
:Parameters:

    base: `str`

    dimsize: `int`, optional

:Returns:

    ncvar: `str`
        NetCDF dimension name or netCDF variable name.
    
        '''
        g = self.write_vars

        ncvar_names = g['ncvar_names']
    
        if dimsize is not None:
            if base in ncvar_names and dimsize == g['ncdim_to_size'][base]:
                # Return the name of an existing netCDF dimension with
                # this size
                return base
        #--- End: if
    
        if base in ncvar_names:
    
            counter = g.setdefault('count_'+base, 1)
        
            ncvar = '{0}_{1}'.format(base, counter)
            while ncvar in ncvar_names:
                counter += 1
                ncvar = '{0}_{1}'.format(base, counter)
        else:
            ncvar = base
    
        ncvar_names.add(ncvar)
    
        return ncvar
    #--- End: def
    
    def _write_attributes(self, parent, ncvar, extra={}, omit=()):
        '''
:Examples 1:

>>> w._write_attributes(x, 'lat')
    
:Parameters:

    parent:

    ncvar: `str`

    extra: `dict`, optional
    
    omit: sequence of `str`, optional

:Returns:

    `None`

:Examples 2:
    
        '''
        netcdf_attrs = self.get_properties(parent)

        netcdf_attrs.update(extra)
        netcdf_attrs.pop('_FillValue', None)
    
        for attr in omit:
            netcdf_attrs.pop(attr, None) 
    
        if not netcdf_attrs:
            return
        
        self.write_vars['nc'][ncvar].setncatts(netcdf_attrs)
    #--- End: def
    
    def _character_array(self, array):
        '''Convert a numpy string array to a numpy character array wih an
extra trailing dimension.
    
:Parameters:

    array: `numpy.ndarray`

:Returns:

    out: `numpy.ndarray`

:Examples:

>>> print a, a.shape, a.dtype.itemsize
['fu' 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[['f' 'u' ' ']
 ['b' 'a' 'r']] (2, 3) 1

>>> print a, a.shape, a.dtype.itemsize
[-- 'bar'] (2,) 3
>>> b = _character_array(a)
>>> print b, b.shape, b.dtype.itemsize
[[-- -- --]
 ['b' 'a' 'r']] (2, 3) 1

        '''
        strlen = array.dtype.itemsize
        shape  = array.shape

        new = numpy.ma.masked_all(shape + (strlen,), dtype='S1')
        
        for index in numpy.ndindex(shape):
            value = array[index]
            if value is numpy.ma.masked:
                new[index] = numpy.ma.masked
            else:
                new[index] = tuple(value.ljust(strlen, ' ')) 
        #--- End: for
    
        return new
    #--- End: def
    
    def _datatype(self, variable):
        '''Return the netCDF4.createVariable datatype corresponding to the
datatype of the array of the input variable
    
For example, if variable.dtype is 'float32', then 'f4' will be
returned.
    
Numpy string data types will return 'S1' regardless of the numpy
string length. This means that the required conversion of
multi-character datatype numpy arrays into single-character datatype
numpy arrays (with an extra trailing dimension) is expected to be done
elsewhere (currently in the _write_netcdf_variable method).
    
If the input variable has no `!dtype` attribute (or it is None) then
'S1' is returned.
    
 :Parameters:
 
     variable: 
         Any object with a `!dtype` attribute whose value is a
         `numpy.dtype` object or `None`.
 
 :Returns:
 
     out: `str`
        The `netCDF4.createVariable` data type corresponding to the
        datatype of the array of the input variable.

        '''
        g = self.write_vars

        data = self.get_data(variable, None)
        if data is None:
            return 'S1'

        dtype = getattr(data, 'dtype', None)
        
#        if not hasattr(variable, 'dtype'):
#            dtype = numpy.asanyarray(variable).dtype
        if dtype is None or dtype.char == 'S':
            return 'S1'            
    
#        dtype = variable.dtype
    
        convert_dtype = g['datatype']
    
        new_dtype = convert_dtype.get(dtype, None)
        if new_dtype is not None:
            dtype = new_dtype
            
        return '{0}{1}'.format(dtype.kind, dtype.itemsize)
    #--- End: def
    
    def _string_length_dimension(self, size):
        '''Create, if necessary, a netCDF dimension for string variables.
    
:Parameters:

    size: `int`

:Returns:

    out: `str`
        The netCDF dimension name.

        '''
        g = self.write_vars

        # ----------------------------------------------------------------
        # Create a new dimension for the maximum string length
        # ----------------------------------------------------------------
        ncdim = self._check_name('strlen{0}'.format(size), dimsize=size)
        
        if ncdim not in g['ncdim_to_size']:
            # This string length dimension needs creating
            g['ncdim_to_size'][ncdim] = size
            g['netcdf'].createDimension(ncdim, size)
    
        return ncdim
    #--- End: def
    
    def _netcdf_dimensions(self, field, key):
        '''Return a tuple of the netCDF dimension names for the axes of a
coordinate or cell measures objects.
    
:Parameters:

    field: `Field`

    key: `str`

:Returns:

    out: `tuple`
        The netCDF dimension names.

        '''
        g = self.write_vars
                
        return tuple([g['axis_to_ncdim'][axis]
                      for axis in self._get_construct_axes(field, key)])
    #--- End: def
        
    def _create_netcdf_variable_name(self, parent, default):
        '''asdasdasd
        
:Parameter:
        
    parent:
           
    default: `str`
    
        '''
        ncvar = self.get_ncvar(parent, None)
        if ncvar is None:
            try:
                ncvar = self.get_property(parent, 'standard_name', default)
            except AttributeError:
                ncvar = default
                
        return self._check_name(ncvar)
    #--- End: def
    
#    def _data_ncvar(self, ncvar):
#        '''
#        
#:Parmaeters:
#    
#    data: `Data`
#           
#    ncvar: `str`
#    
#        '''
#        g = self.write_vars
#        
#        return self._check_name(ncvar, None)
#    #--- End: def
    
    def _write_dimension(self, ncdim, f, axis, unlimited=False):
        '''Write a netCDF dimension to the file.
    
:Parameters:
    
    ncdim: `str`
        The netCDF dimension name.

    f: `Field`
   
    axis: `str`
        The field's domain axis identifier.

    unlimited: `bool`, optional
        If true then create an unlimited dimension. By default
        dimensions are not unlimited.

:Returns:

    `None`
        
        '''
        g = self.write_vars
        _debug = g['_debug']
        
        if g['verbose'] or _debug:
            domain_axis = self._get_domain_axes(f)[axis]
            print '    Writing', repr(domain_axis), 'to netCDF dimension:', ncdim

        size = self._get_domain_axis_size(f, axis)
        
        g['ncdim_to_size'][ncdim] = size
        g['axis_to_ncdim'][axis] = ncdim

        if unlimited:
            # Create an unlimited dimension
            try:
                g['netcdf'].createDimension(ncdim, None)
            except RuntimeError as error:
    
                message = "Can't create unlimited dimension in {} file ({}).".format(
                    g['netcdf'].file_format, error)
    
                error = str(error)
                if error == 'NetCDF: NC_UNLIMITED size already in use':
                    raise RuntimeError(
message+" Only one unlimited dimension allowed. Consider using a netCDF4 format.")
                    
                raise RuntimeError(message)
        else:
            try:
                g['netcdf'].createDimension(ncdim, size)
            except RuntimeError as error:
                raise RuntimeError(
                    "Can't create dimension of size {} in {} file ({})".format(
                        size, g['netcdf'].file_format, error))
    #--- End: def
    
#    def _change_reference_datetime(self, coord):
#        '''
#    
#    :Parameters:
#    
#        coord : `Coordinate`
#    
#    :Returns:
#    
#        out : `Coordinate`
#    
#    '''
#        g = self.write_vars
#
#        if not coord.Units.isreftime:
#            return coord
#    
#        reference_datetime = g['reference_datetime']
#        if not reference_datetime:
#            return coord
#    
#        coord2 = coord.copy()
#        try:
#            coord2.reference_datetime = reference_datetime
#        except ValueError:
#            raise ValueError(
#    "Can't override coordinate reference date-time {!r} with {!r}".format(
#        coord.reference_datetime, reference_datetime))
#    
#        return coord2
#    #--- End: def
    
    def _write_dimension_coordinate(self, f, key, coord):
        '''Write a coordinate variable and its bound variable to the file.
    
This also writes a new netCDF dimension to the file and, if required,
a new netCDF dimension for the bounds.

:Parameters:

    f: `Field`
   
    key: `str`

    coord: `DimensionCoordinate`

:Returns:

    out: `str`
        The netCDF name of the dimension coordinate.

        '''
        g = self.write_vars

        seen = g['seen']
    
#        coord = self._change_reference_datetime(coord)

        axis = self._get_construct_axes(f, key)[0]

        create = False
        if not self._already_in_file(coord):
            create = True
        elif seen[id(coord)]['ncdims'] != ():
            if seen[id(coord)]['ncvar'] != seen[id(coord)]['ncdims'][0]:
                # Already seen this coordinate but it was an auxiliary
                # coordinate, so it needs to be created as a dimension
                # coordinate.
                create = True
        #--- End: if
    
        if create:
            ncvar = self._create_netcdf_variable_name(coord,
                                                      default='coordinate')
            
            # Create a new dimension, if it is not a scalar coordinate
            if self.get_ndim(coord) > 0:
                unlimited = self._unlimited(f, axis)
                self._write_dimension(ncvar, f, axis, unlimited=unlimited)
    
            ncdimensions = self._netcdf_dimensions(f, key)
            
            # If this dimension coordinate has bounds then write the
            # bounds to the netCDF file and add the 'bounds' or
            # 'climatology' attribute to a dictionary of extra
            # attributes
            extra = self._write_bounds(coord, ncdimensions, ncvar)
    
            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, ncdimensions, coord, extra=extra)
        else:
            ncvar = seen[id(coord)]['ncvar']

        g['key_to_ncvar'][key] = ncvar
    
        g['axis_to_ncdim'][axis] = ncvar

        return ncvar
    #--- End: def
    
    def _write_scalar_data(self, value, ncvar):
        '''Write a dimension coordinate and bounds to the netCDF file.
    
    This also writes a new netCDF dimension to the file and, if required,
    a new netCDF bounds dimension.
    
    .. note:: This function updates ``g['seen']``.
    
    :Parameters:
    
        data: `Data`
       
        ncvar: `str`
    
    :Returns:
    
        out: `str`
            The netCDF name of the scalar data variable
    
        '''
        g = self.write_vars

        seen = g['seen']
    
        create = not self._already_in_file(value, ncdims=())
    
        if create:
            ncvar = self._check_name(ncvar) # DCH ?
            
            # Create a new dimension coordinate variable
            self._write_netcdf_variable(ncvar, (), value)
        else:
            ncvar = seen[id(value)]['ncvar']
    
        return ncvar
    #--- End: def
    
    def _already_in_file(self, variable, ncdims=None, ignore_type=False):
        '''Return True if a variable is logically equal any variable in the
g['seen'] dictionary.
    
If this is the case then the variable has already been written to the
output netCDF file and so we don't need to do it again.
    
If 'ncdims' is set then a extra condition for equality is applied,
namely that of 'ncdims' being equal to the netCDF dimensions (names
and order) to that of a variable in the g['seen'] dictionary.
    
When True is returned, the input variable is added to the g['seen']
dictionary.
    
:Parameters:
    
    variable : 

    ncdims : tuple, optional

:Returns:

    out: `bool`
        True if the variable has already been written to the file,
        False otherwise.

        '''
        g = self.write_vars

        seen = g['seen']
    
        for value in seen.itervalues():
            if ncdims is not None and ncdims != value['ncdims']:
                # The netCDF dimensions (names and order) of the input
                # variable are different to those of this variable in
                # the 'seen' dictionary
                continue
    
            # Still here?
            if variable.equals(value['variable'], ignore_construct_type=ignore_type):
                seen[id(variable)] = {'variable': variable,
                                      'ncvar'   : value['ncvar'],
                                      'ncdims'  : value['ncdims']}
                return True
        #--- End: for
        
        return False
    #--- End: def
    
    def _write_bounds(self, coord, coord_ncdimensions, coord_ncvar):
        '''Create a bounds netCDF variable, creating a new bounds netCDF
    dimension if required. Return the bounds variable's netCDF variable
    name.
    
    .. note:: This function updates ``g['netcdf']``.
    
    :Parameters:
    
        coord: `BoundedVariable`
    
        coord_ncdimensions: `tuple`
            The ordered netCDF dimension names of the coordinate's
            dimensions (which do not include the bounds dimension).
    
        coord_ncvar: `str`
            The netCDF variable name of the parent variable
    
    :Returns:
    
        out: `dict`
    
    :Examples:
    
    >>> extra = _write_bounds(c, ('dim2',))
    
        '''
        g = self.write_vars

#        bounds = coord.get_bounds(None)
        bounds = self._get_bounds(coord, None)
        if bounds is None:
            return {}

        data = self.get_data(bounds, None) 
        if data is None:
            return {}

        # Still here? Then this coordinate has a bounds attribute
        # which contains data.
        extra = {}
        
        size = data.shape[-1]
    
        ncdim = self._check_name('bounds{0}'.format(size), dimsize=size)
    
        # Check if this bounds variable has not been previously
        # created.
        ncdimensions = coord_ncdimensions +(ncdim,)        
        if self._already_in_file(bounds, ncdimensions):
            # This bounds variable has been previously created, so no
            # need to do so again.
            ncvar = g['seen'][id(bounds)]['ncvar']
    
        else:
    
            # This bounds variable has not been previously created, so
            # create it now.
            ncdim_to_size = g['ncdim_to_size']
            if ncdim not in ncdim_to_size:
                if g['verbose'] or g['_debug']:
                    print '    Writing size', size, 'netCDF dimension for bounds:', ncdim
                    
                ncdim_to_size[ncdim] = size
                g['netcdf'].createDimension(ncdim, size)
             
            ncvar = self.get_ncvar(bounds, coord_ncvar+'_bounds')                
            ncvar = self._check_name(ncvar)
            
            # Note that, in a field, bounds always have equal units to
            # their parent coordinate
    
            # Select properties to omit
            omit = []
            for prop in g['omit_bounds_properties']:
                if self.has_property(coord, prop):
                    omit.append(prop)
            #--- End: for
    
            # Create the bounds netCDF variable
            self._write_netcdf_variable(ncvar, ncdimensions, bounds,
                                        omit=omit)
        #--- End: if
    
        if getattr(coord, 'climatology', None):
            extra['climatology'] = ncvar
        else:
            extra['bounds'] = ncvar
    
        g['bounds'][coord_ncvar] = ncvar
            
        return extra
    #--- End: def
            
    def _write_scalar_coordinate(self, f, axis, coord, coordinates,
                                 extra={}):
        '''Write a scalar coordinate and its bounds to the netCDF file.
    
It is assumed that the input coordinate is has size 1, but this is not
checked.
    
If an equal scalar coordinate has already been written to the file
then the input coordinate is not written.
    
:Parameters:

    f: `Field`
   
    axis : str
        The field's axis identifier for the scalar coordinate.

    coordinates: `list`

:Returns:

    coordinates: `list`
        The updated list of netCDF auxiliary coordinate names.

        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
            
#        coord = self._squeeze_coordinate(coord)
        coord = self._squeeze(coord, axes=0, copy=True)
    
        if not self._already_in_file(coord, ()):
            ncvar = self._write_netcdf_variable_name(coord,
                                                     default='scalar',
                                                     extra=extra)
    
            # If this scalar coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            bounds_extra = self._write_bounds(coord, (), ncvar)
    
            # Create a new auxiliary coordinate variable
            self._write_netcdf_variable(ncvar, (), coord, extra=bounds_extra)
    
        else:
            # This scalar coordinate has already been written to the
            # file
            ncvar = g['seen'][id(coord)]['ncvar']
    
        g['axis_to_ncscalar'][axis] = ncvar
    
        g['key_to_ncvar'][axis] = ncvar
    
        coordinates.append(ncvar)
    
        return coordinates
    #--- End: def
    
#    def _squeeze_coordinate(self, coord):
#        '''
#        '''
#        return coord.squeeze(axes=0, copy=True)
#        
#        coord = coord.copy()
#        
#        coord.data._array = numpy.squeeze(coord.data.get_array())
#        if coord.has_bounds():
#            array = coord.bounds.data.get_array()
#            array = Data(numpy.squeeze(array, axis=0)
#            coord.bounds.set_data(array._array = numpy.squeeze(coord.bounds.data.get_array(), axis=0)
#    
#        return coord
    #--- End: def

    def _squeeze(self, construct, axes=None, copy=True):
        '''
        '''
        return construct.squeeze(axes=axes, copy=copy)
        
#        coord = coord.copy()
#        
#        coord.data._array = numpy.squeeze(coord.data.get_array())
#        if coord.has_bounds():
#            array = coord.bounds.data.get_array()
#            array = Data(numpy.squeeze(array, axis=0)
#            coord.bounds.set_data(array._array = numpy.squeeze(coord.bounds.data.get_array(), axis=0)
#    
#        return coord
    #--- End: def
    
    def _expand_dims(self, construct, position=0, axis=None, copy=True):
        '''
        '''
        return construct.expand_dims(position=position, axis=axis, copy=copy)
        
#        coord = coord.copy()
#        
#        coord.data._array = numpy.squeeze(coord.data.get_array())
#        if coord.has_bounds():
#            array = coord.bounds.data.get_array()
#            array = Data(numpy.squeeze(array, axis=0)
#            coord.bounds.set_data(array._array = numpy.squeeze(coord.bounds.data.get_array(), axis=0)
#    
#        return coord
    #--- End: def
    
    def _write_auxiliary_coordinate(self, f, key, coord, coordinates):
        '''
    
    Write an auxiliary coordinate and its bounds to the netCDF file.
    
    If an equal auxiliary coordinate has already been written to the file
    then the input coordinate is not written.
    
    :Parameters:
    
        f : `Field`
       
        key : str
    
        coord : `Coordinate`
    
        coordinates : list
    
    :Returns:
    
        coordinates : list
            The list of netCDF auxiliary coordinate names updated in
            place.
    
    :Examples:
    
    >>> coordinates = _write_auxiliary_coordinate(f, 'aux2', coordinates)
    
        '''
        g = self.write_vars

#        coord = self._change_reference_datetime(coord)
    
        ncdimensions = self._netcdf_dimensions(f, key)
    
        if self._already_in_file(coord, ncdimensions):
            ncvar = g['seen'][id(coord)]['ncvar']
        
        else:
            ncvar = self._create_netcdf_variable_name(coord,
                                                      default='auxiliary')
            
            # If this auxiliary coordinate has bounds then create the
            # bounds netCDF variable and add the bounds or climatology
            # attribute to the dictionary of extra attributes
            extra = self._write_bounds(coord, ncdimensions, ncvar)
    
            # Create a new auxiliary coordinate variable
            self._write_netcdf_variable(ncvar, ncdimensions, coord,
                                        extra=extra)
    
        g['key_to_ncvar'][key] = ncvar
    
        coordinates.append(ncvar)
    
        return coordinates
    #--- End: def
      
    def _write_domain_ancillary(self, f, key, anc):
        '''Write a domain ancillary and its bounds to the netCDF file.
    
If an equal domain ancillary has already been written to the file athen
it is not re-written.

:Examples 1:

>>> ncvar = w._write_domain_ancillary(f, 'domainancillary2', d)
    
:Parameters:

    f: `Field`
   
    key: `str`
        The internal identifier of the domain ancillary object.

    anc: `DomainAncillary`
    
:Returns:

    out: `str`
        The netCDF variable name of the domain ancillary variable.

:Examples 2:

        '''
        g = self.write_vars

        ncdimensions = tuple([g['axis_to_ncdim'][axis]
                              for axis in self._get_construct_axes(f, key)])
    
        create = not self._already_in_file(anc, ncdimensions, ignore_type=True)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']
        
        else:
            # See if we can set the default netCDF variable name to
            # its formula_terms term
            default = None
            for ref in self.get_coordinate_references(f).itervalues():
                for term, da_key in ref.coordinate_conversion.domain_ancillaries().iteritems():
                    if da_key == key:
                        default = term
                        break
                #--- End: for
                if default is not None:
                    break
            #--- End: for
            if default is None:
                default='domain_ancillary'
                
            ncvar = self._create_netcdf_variable_name(anc,
                                                      default=default)
    
            # If this domain ancillary has bounds then create the bounds
            # netCDF variable
            self._write_bounds(anc, ncdimensions, ncvar)
    
            self._write_netcdf_variable(ncvar, ncdimensions, anc)
        #--- End: if
    
        g['key_to_ncvar'][key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_field_ancillary(self, f, key, anc):
        '''Write a field ancillary to the netCDF file.
    
If an equal field ancillary has already been written to the file then
it is not re-written.
    
:Parameters:

    f : `Field`
   
    key : str

    anc : `FieldAncillary`

:Returns:

    out: `str`
        The netCDF variable name of the field ancillary object.

:Examples:

>>> ncvar = _write_field_ancillary(f, 'fieldancillary2', anc)

    '''
        g = self.write_vars

        ncdimensions = tuple([g['axis_to_ncdim'][axis]
                              for axis in self._get_construct_axes(f, key)])
    
        create = not self._already_in_file(anc, ncdimensions)
    
        if not create:
            ncvar = g['seen'][id(anc)]['ncvar']    
        else:
            ncvar = self._create_netcdf_variable_name(anc, default='ancillary_data')
            self._write_netcdf_variable(ncvar, ncdimensions, anc)
    
        g['key_to_ncvar'][key] = ncvar
    
        return ncvar
    #--- End: def
      
    def _write_cell_measure(self, field, key, cell_measure):
        '''Write a cell measure construct to the netCDF file.

If an identical construct has already in the file then the cell
measure will not be written.

:Parameters:

    field: `Field`
        The field containing the cell measure.

    key: `str`
        The identifier of the cell measure (e.g. 'msr0').

    cell_measure: `CellMeasure`

:Returns:

    out: `str`
        The 'measure: ncvar'.

:Examples:

        '''
        g = self.write_vars

        measure = self.get_measure(cell_measure)
        if measure is None:
            raise ValueError(
"Can't create a netCDF cell measure variable without a 'measure' property")

        ncdimensions = self._netcdf_dimensions(field, key)
    
        if self._already_in_file(cell_measure, ncdimensions):
            # Use existing cell measure variable
            ncvar = g['seen'][id(cell_measure)]['ncvar']
        else:
            # Create a new cell measure variable
            ncvar = self._create_netcdf_variable_name(cell_measure, default='cell_measure')
            self._write_netcdf_variable(ncvar, ncdimensions, cell_measure)
                
        g['key_to_ncvar'][key] = ncvar
    
        # Update the cell_measures list
        return '{0}: {1}'.format(measure, ncvar)
    #--- End: def
      
    def _write_grid_mapping(self, f, ref, multiple_grid_mappings):
        '''Write a grid mapping georeference to the netCDF file.
    
.. note:: This function updates ``grid_mapping``, ``g['seen']``.

:Parameters:

    f: `Field`

    ref: `CoordinateReference`
        The grid mapping coordinate reference to write to the file.

    multiple_grid_mappings: `bool`

:Returns:

    out: `str`

:Examples:

        '''
        g = self.write_vars

        _debug = g['_debug']
        
        if self._already_in_file(ref):
            # Use existing grid_mapping variable
            ncvar = g['seen'][id(ref)]['ncvar']
    
        else:
            # Create a new grid mapping variable
            default = self.get_coordinate_conversion_parameters(ref).get(
                'grid_mapping_name', 'grid_mapping')
            ncvar = self._create_netcdf_variable_name(ref, default=default)

            if g['verbose'] or _debug:
                print '    Writing', repr(ref), 'to netCDF variable:', ncvar

            g['nc'][ncvar] = g['netcdf'].createVariable(ncvar, 'S1', (),
                                                        endian=g['endian'],
                                                        **g['compression'])
    
#            cref = ref.copy()
#            cref = ref.canonical(f) # NOTE: NOT converting units
    
            # Add named parameters
            parameters = self.get_coordinate_conversion_parameters(ref)
            parameters.update(self.get_datum_parameters(ref))
            
            for term, value in parameters.items():
                if value is None:
                    del parameters[term]
                    continue
                
                if numpy.size(value) == 1:
                    value = numpy.array(value, copy=False).item()
                else:
                    value = numpy.array(value, copy=False).tolist()

                parameters[term] = value
            #--- End: for

            # Add the grid mapping name property
            grid_mapping_name = self.get_coordinate_conversion_parameters(ref).get(
                'grid_mapping_name', None)
            if grid_mapping_name is not None:
                parameters['grid_mapping_name'] = grid_mapping_name
                
            g['nc'][ncvar].setncatts(parameters)
            
            # Update the 'seen' dictionary
            g['seen'][id(ref)] = {'variable': ref, 
                                  'ncvar'   : ncvar,
                                  'ncdims'  : (), # Grid mappings have no netCDF dimensions
                              }
        #--- End: if

        if multiple_grid_mappings:
            return '{0}: {1}'.format(
                ncvar,
                ' '.join(
                    sorted([g['key_to_ncvar'][key]
                            for key in self.get_coordinate_reference_coordinates(ref)])))
        else:
            return ncvar
    #--- End: def
    
    def _write_netcdf_variable(self, ncvar, ncdimensions, cfvar,
                               omit=(), extra={}, fill=True):
        '''Create a netCDF variable from *cfvar* with name *ncvar* and
dimensions *ncdimensions*. The new netCDF variable's properties are
given by cfvar.properties(), less any given by the *omit* argument. If
a new string-length netCDF dimension is required then it will also be
created. The ``seen`` dictionary is updated for *cfvar*.
    
:Parameters:

    ncvar: `str`
        The netCDF name of the variable.

    dimensions: `tuple`
        The netCDF dimension names of the variable

    cfvar: `Variable`
        The coordinate, cell measure or field object to write to the
        file.

    omit: sequence of `str`, optional

    extra: `dict`, optional

:Returns:

    `None`

        '''
        g = self.write_vars
                
        _debug = g['_debug']
        
        if g['verbose'] or _debug:
            print '    Writing', repr(cfvar), 'to netCDF variable:', ncvar
     
        # ------------------------------------------------------------
        # Set the netCDF4.createVariable datatype
        # ------------------------------------------------------------
        datatype = self._datatype(cfvar)
    
        data = self.get_data(cfvar, None)

        if data is not None and datatype == 'S1':
            # --------------------------------------------------------
            # Convert a string data type numpy array into a
            # character data type ('S1') numpy array with an extra
            # trailing dimension.
            # --------------------------------------------------------
            strlen = data.dtype.itemsize
            if strlen > 1:
                data = self._convert_to_char(data)
                ncdim = self._string_length_dimension(strlen)            
                ncdimensions = ncdimensions + (ncdim,)
        #--- End: if

        # ------------------------------------------------------------
        # Find the fill value - the value that the variable's data get
        # filled before any data is written. if the fill value is
        # False then the variable is not pre-filled.
        # ------------------------------------------------------------
        if fill:
            fill_value = getattr(cfvar, '_FillValue', None)
        else:
            fill_value = False
    
        if getattr(cfvar, 'isfield', False):
            lsd = g['least_significant_digit']
        else:
            lsd = None
    
        # Set HDF chunk sizes
        chunksizes = None
    #    chunksizes = [size for i, size in sorted(cfvar.HDF_chunks().items())]
    #    if chunksizes == [None] * cfvar.data.ndim:
    #        chunksizes = None
    #
    #    if _debug:
    #        print '  chunksizes:', chunksizes

        # ------------------------------------------------------------
        # Create a new netCDF variable
        # ------------------------------------------------------------ 
        try:
            g['nc'][ncvar] = g['netcdf'].createVariable(
                ncvar,
                datatype, 
                ncdimensions,
                fill_value=fill_value,
                least_significant_digit=lsd,
                endian=g['endian'],
                chunksizes=chunksizes,
                **g['compression'])
        except RuntimeError as error:
            error = str(error)
            if error == 'NetCDF: Not a valid data type or _FillValue type mismatch':
                raise ValueError(
"Can't write {} data from {!r} to a {} file. Consider using a netCDF4 format or use the 'single' or 'datatype' parameters or change the datatype before writing.".format(
    cfvar.dtype.name, cfvar, g['netcdf'].file_format))
                
            message = "Can't create variable in {} file from {} ({})".format(
                g['netcdf'].file_format, cfvar, error)

            if error == 'NetCDF: NC_UNLIMITED in the wrong index':            
                raise RuntimeError(
message+". Unlimited dimension must be the first (leftmost) dimension of the variable. Consider using a netCDF4 format.")
                    
            raise RuntimeError(message)
        #--- End: try

        #-------------------------------------------------------------
        # Write attributes to the netCDF variable
        #-------------------------------------------------------------
        self._write_attributes(cfvar, ncvar, extra=extra, omit=omit)
    
        #-------------------------------------------------------------
        # Write data to the netCDF variable
        #
        # Note that we don't need to worry about scale_factor and
        # add_offset, since if a data array is *not* a numpy array,
        # then it will have its own scale_factor and add_offset
        # parameters which will be applied when the array is realised,
        # and the python netCDF4 package will deal with the case when
        # scale_factor or add_offset are set as properties on the
        # variable.
        # ------------------------------------------------------------
        if data is not None:  
            # Find the missing data values, if any.
            _FillValue    = self.get_property(cfvar, '_FillValue', None) 
            missing_value = self.get_property(cfvar, 'missing_value', None)
            unset_values = [value for value in (_FillValue, missing_value)
                            if value is not None]
            self._write_data(data, ncvar, unset_values)
    
        # Update the 'seen' dictionary
        g['seen'][id(cfvar)] = {'variable': cfvar,
                                'ncvar'   : ncvar,
                                'ncdims'  : ncdimensions}
    #--- End: def
    
    def _write_data(self, data, ncvar, unset_values=()):
        '''

:Parameters:

    data: `Data`

    ncvar: `str`

    unset_values: sequence of numbers

        '''
        g = self.write_vars

        convert_dtype = g['datatype']

        # Get the data as a numpy array
        array = self._get_array(data)

        # Convert data type
        new_dtype = convert_dtype.get(array.dtype, None)
        if new_dtype is not None:
            array = array.astype(new_dtype)  

        # Check that the array doesn't contain any elements
        # which are equal to any of the missing data values
        if unset_values:
            if numpy.ma.is_masked(array):
                temp_array = array.compressed()
            else:
                temp_array = array
                
            if numpy.intersect1d(unset_values, temp_array):
                raise ValueError(
"ERROR: Can't write data that has _FillValue or missing_value at unmasked point: {!r}".format(cfvar))
        #--- End: if
    
        # Copy the array into the netCDF variable
        g['nc'][ncvar][...] = array
    #--- End: def
    
    def _convert_to_char(self, data):
        '''Convert string data into character data

The return `Data` object will have data type 'S1' and will have an
extra trailing dimension.
    
:Parameters:
    
    data: `Data`

:Returns:

    out: `Data`

        '''
        strlen = data.dtype.itemsize
        if strlen > 1:
            char_array = self._character_array(self._get_array(data))
            data = type(data)(char_array, source=data, copy=False)
    
        return data
    #--- End: def
    
    def _write_field(self, f, add_to_seen=False,
                     allow_data_expand_dims=True):
        '''
    
:Parameters:

    f : `Field`

    add_to_seen : bool, optional

    allow_data_expand_dims: `bool`, optional

:Returns:

    `None`

        '''
        g = self.write_vars

        _debug = g['_debug']
        if _debug:
            print '  Writing', repr(f)+':'
            
        seen = g['seen']
          
        if add_to_seen:
            id_f = id(f)
            org_f = f
            
        f = self.copy_field(f)
    
        data_axes = self._get_data_axes(f)
    
        # Mapping of domain axis identifiers to netCDF dimension names
        g['axis_to_ncdim'] = {}
    
        # Mapping of domain axis identifiers to netCDF scalar
        # coordinate variable names
        g['axis_to_ncscalar'] = {}
    
        # Mapping of field component internal identifiers to netCDF
        # variable names
        #
        # For example: {'dimensioncoordinate1': 'longitude'}
        g['key_to_ncvar'] = {}
    
        # Initialize the list of the field's auxiliary/scalar coordinates
        coordinates = []

        formula_terms_refs = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('standard_name', False)]

        grid_mapping_refs = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('grid_mapping_name', False)]

        owning_coordinates = []
        computed_standard_names = []
        for ref in formula_terms_refs:
            coord_key = None
            computed_standard_name = self.get_coordinate_conversion_parameters(ref).get(
                'computed_standard_name')
            
            if computed_standard_name is not None:
                standard_name = self.get_coordinate_conversion_parameters(ref).get('standard_name')
                if standard_name is not None:
                    for key in self.get_coordinate_reference_coordinates(ref):
                        coord = self.get_coordinates(f)[key]
                        if (self.get_ndim(coord) == 1 and                        
                            self.get_property(coord, 'standard_name', None) == standard_name):
                            if coord_key is not None:
                                coord_key = None
                                break

                            coord_key = key
            #--- End: if
                
            owning_coordinates.append(key)
            computed_standard_names.append(computed_standard_name)
        #--- End: for
    
        dimension_coordinates = self.get_dimension_coordinates(f)
        
        # For each of the field's axes ...
        for axis in sorted(self._get_domain_axes(f)):
            found_dimension_coordinate = False
            for key, dim_coord in dimension_coordinates.iteritems():
                if self._get_construct_axes(f, key) != (axis,):
                    continue

                # --------------------------------------------------------
                # Still here? Then a dimension coordinate exists for
                # this domain axis.
                # --------------------------------------------------------
                if axis in data_axes:
                    # The data array spans this domain axis, so write
                    # the dimension coordinate to the file as a
                    # coordinate variable.
                    ncvar = self._write_dimension_coordinate(f, key, dim_coord)
                else:
                    # The data array does not span this axis (and
                    # therefore it must have size 1).
                    if len(self._get_constructs(f, axes=[axis])) >= 2:
                        # There ARE auxiliary coordinates, cell
                        # measures, domain ancillaries or field
                        # ancillaries which span this domain axis, so
                        # write the dimension coordinate to the file
                        # as a coordinate variable.
                        ncvar = self._write_dimension_coordinate(f, key, dim_coord)
    
                        # Expand the field's data array to include
                        # this domain axis
                        f = self._expand_dims(f, position=0, axis=axis, copy=False) 
                    else:
                        # There are NO auxiliary coordinates, cell
                        # measures, domain ancillaries or field
                        # ancillaries which span this domain axis, so
                        # write the dimension coordinate to the file
                        # as a scalar coordinate variable.
                        if key in owning_coordinates:
                            i = owning_coordinates.index(key)
                            ref = formula_terms_refs[i]
                            computed_standard_name = self.get_coordinate_reference_parameters(ref).get(
                                'computed_standard_name', None)
                            if computed_standard_name is not None:
                                self.set_property(dim_coord, 'computed_standard_name',
                                                  computed_standard_name)
                        #--- End: if
                            
                        coordinates = self._write_scalar_coordinate(f, axis, dim_coord,
                                                                    coordinates)
                #-- End: if

                found_dimension_coordinate = True
                break
            #--- End: for

            if not found_dimension_coordinate:
                # --------------------------------------------------------
                # There is no dimension coordinate for this axis
                # --------------------------------------------------------
#                if axis not in data_axes and f.items(role=('a', 'm', 'c', 'f'), axes=axis):
#                if axis not in data_axes and f.constructs(axes=[axis]):
                if axis not in data_axes and self._get_constructs(f, axes=[axis]):
                    # The data array doesn't span the domain axis but
                    # an auxiliary coordinate, cell measure, domain
                    # ancillary or field ancillary does, so expand the
                    # data array to include it.
                    f = self._expand_dims(f, position=0, axis=axis, copy=False)
                    data_axes.append(axis)
    
                # If the data array (now) spans this domain axis then create a
                # netCDF dimension for it
                if axis in data_axes:
                    ncdim = getattr(f, 'ncdimensions', {}).get(axis, 'dim')
                    ncdim = self._check_name(ncdim)
    
                    unlimited = self._unlimited(f, axis)
                    self._write_dimension(ncdim, f, axis, unlimited=unlimited)
            #--- End: if
    
        #--- End: for
    
        # ----------------------------------------------------------------
        # Create auxiliary coordinate variables, except those which might
        # be completely specified elsewhere by a transformation.
        # ----------------------------------------------------------------
        # Initialize the list of 'coordinates' attribute variable values
        # (each of the form 'name')
        for key, aux_coord in sorted(self._get_auxiliary_coordinates(f).iteritems()):
            coordinates = self._write_auxiliary_coordinate(f, key, aux_coord,
                                                           coordinates)
    
        # ------------------------------------------------------------
        # Create netCDF variables from domain ancillaries
        # ------------------------------------------------------------
        for key, anc in sorted(self._get_domain_ancillaries(f).iteritems()):
            self._write_domain_ancillary(f, key, anc)
    
        # ------------------------------------------------------------
        # Create netCDF variables from cell measures 
        # ------------------------------------------------------------
        # Set the list of 'cell_measures' attribute values (each of
        # the form 'measure: name')
        cell_measures = [self._write_cell_measure(f, key, msr)
                         for key, msr in sorted(self._get_cell_measures(f).iteritems())]
        
        formula_terms_refs = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('standard_name', False)]

        grid_mapping_refs = [
            ref for ref in self.get_coordinate_references(f).values()
            if self.get_coordinate_conversion_parameters(ref).get('grid_mapping_name', False)]
        
        # ------------------------------------------------------------
        # Create netCDF formula_terms attributes from vertical
        # coordinate references
        # ------------------------------------------------------------
        for ref in formula_terms_refs:
            formula_terms = []
            bounds_formula_terms = []
            owning_coord = None
            
            standard_name = self.get_coordinate_conversion_parameters(ref).get('standard_name')
            if standard_name is not None:
#                c = [(key, coord) for key, coord in self.get_coordinates(f).items()
#                     if self.get_property(coord, 'standard_name', None) == standard_name]
                c = []
                for key in self.get_coordinate_reference_coordinates(ref):
                    coord = self.get_coordinates(f)[key]
                    if self.get_property(coord, 'standard_name', None) == standard_name:
                        c.append((key, coord))

                if len(c) == 1:
                    owning_coord_key, owning_coord = c[0]
            #--- End: if
    
            z_axis = self._get_construct_axes(f, owning_coord_key)[0]
                
            if owning_coord is not None:
                # This formula_terms coordinate reference matches up with
                # an existing coordinate
    
                for term, value in self.get_coordinate_conversion_parameters(ref).iteritems():
                    if value is None:
                        continue
    
                    if term in ('standard_name', 'computed_standard_name'):
                        continue
    
                    ncvar = self._write_scalar_data(value, ncvar=term)
    
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
                    bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                #--- End: for
            
                for term, key in ref.coordinate_conversion.domain_ancillaries().iteritems():
                    if key is None:
                        continue
    
                    domain_anc = self._get_domain_ancillaries(f)[key]
                    if domain_anc is None:
                        continue
    
                    if id(domain_anc) not in seen:
                        continue
    
                    # Get the netCDF variable name for the domain
                    # ancillary and add it to the formula_terms attribute
                    ncvar = seen[id(domain_anc)]['ncvar']                
                    formula_terms.append('{0}: {1}'.format(term, ncvar))
    
                    bounds = g['bounds'].get(ncvar, None)
                    if bounds is not None:
                        if z_axis not in self._get_construct_axes(f, key):
                            bounds = None
    
                    if bounds is None:        
                        bounds_formula_terms.append('{0}: {1}'.format(term, ncvar))
                    else:
                        bounds_formula_terms.append('{0}: {1}'.format(term, bounds))
            #--- End: if

            # Add the formula_terms attribute to the parent coordinate
            # variable
            if formula_terms:
                ncvar = seen[id(owning_coord)]['ncvar']
                formula_terms = ' '.join(formula_terms)
                g['nc'][ncvar].setncattr('formula_terms', formula_terms)
                if g['_debug']:
                    print '    Writing formula_terms to netCDF variable', ncvar+':', repr(formula_terms)
    
                # Add the formula_terms attribute to the parent
                # coordinate bounds variable
                bounds = g['bounds'].get(ncvar)
                if bounds is not None:
                    bounds_formula_terms = ' '.join(bounds_formula_terms)
                    g['nc'][bounds].setncattr('formula_terms', bounds_formula_terms)
                    if g['_debug']:
                        print '    Writing formula_terms to netCDF variable', bounds+':', repr(bounds_formula_terms)
            #--- End: if
                        
            # Deal with a vertical datum
            if owning_coord_key is not None:
                datum = self.get_datum(ref)
                if datum:
                    if g['_debug']:
                        print '    Datum =', datum

                    domain_ancillaries = self.get_datum_domain_ancillaries(ref)

                    count = [0, None]
                    for grid_mapping_ref in grid_mapping_refs:
                        datum1 = self.get_datum(grid_mapping_ref)
                        if not datum1:
                            continue

                        domain_ancillaries1 = self.get_datum_domain_ancillaries(
                            grid_mapping_ref)
                         
                        if (datum.equals(datum1) and
                            domain_ancillaries == domain_ancillaries1):
                            count = [count[0] + 1, grid_mapping_ref]
                            if count[0] > 1:
                                break
                    #--- End: for
    
                    if count[0] == 1:
                        # Add the vertical coordinate to an existing
                        # horizontal coordinate reference
                        grid_mapping_ref = count[1]
                        print 'KKKKKKKKKKKKKKKKKKK', owning_coord_key
                        self.set_coordinate_reference_coordinate(grid_mapping_ref,
                                                                 owning_coord_key)
                    else:
                        # Create a new horizontal coordinate reference for
                        # the vertical datum
                        
                        new_grid_mapping = self.initialise(
                            'CoordinateReference',
                            coordinates=(owning_coord_key,),
                            datum_parameters=self.get_datum_parameters(ref),
                            datum_domain_ancillaries=domain_ancillaries)
                        
                        grid_mapping_refs.append(new_grid_mapping)
            #--- End: if
        #--- End: for
    
        # ------------------------------------------------------------
        # Create netCDF variables grid mappings
        # ------------------------------------------------------------
        multiple_grid_mappings = (len(grid_mapping_refs) > 1)
        
        grid_mapping = [self._write_grid_mapping(f, ref, multiple_grid_mappings)
                        for ref in grid_mapping_refs]
        
#        grid_mapping = [self._write_grid_mapping(f, ref, multiple_grid_mappings)
#                        for ref in grid_mapping_refs]

#        if  multiple_grid_mappings:
#            grid_mapping2 = []
#            for x in grid_mapping:
#                grid_mapping_variable, coordinate_variables = x.split(':')
#                coordinate_variables = coordinate_variables.split()
#                for y in grid_mapping:
#                    if y == coordinate_variables:
#                        continue
#
#                    coordinate_variables1 = y.split(':')[1].split()
#    
#                    if (len(coordinate_variables1) <= len(coordinate_variables) and
#                        set(coordinate_variables1).issubset(coordinate_variables)):
#                        coordinate_variables = [c for c in coordinate_variables
#                                                if c not in coordinate_variables1]
#                #--- End: for
#                grid_mapping2.apend(grid_mapping_variable+':'+' '.join(coordinate_variables))
#            #--- End: for
#            grid_mapping = grid_mapping2
#        #--- End: if
    
        # ----------------------------------------------------------------
        # Field ancillary variables
        # ----------------------------------------------------------------
        # Create the 'ancillary_variables' CF-netCDF attribute and create
        # the referenced CF-netCDF ancillary variables
        ancillary_variables = [self._write_field_ancillary(f, key, anc)
                               for key, anc in self.get_field_ancillaries(f).iteritems()]
    
        # ----------------------------------------------------------------
        # Create the CF-netCDF data variable
        # ----------------------------------------------------------------
        ncvar = self._create_netcdf_variable_name(f, default='data')
    
        ncdimensions = tuple([g['axis_to_ncdim'][axis] for axis in self._get_data_axes(f)])
    
        extra = {}

        # Cell measures
        if cell_measures:
            cell_measures = ' '.join(cell_measures)
            if _debug:
                print '    Writing cell_measures to netCDF variable', ncvar+':', cell_measures
                
            extra['cell_measures'] = cell_measures
            
        # Auxiliary/scalar coordinates
        if coordinates:
            coordinates = ' '.join(coordinates)
            if _debug:
                print '    Writing coordinates to netCDF variable', ncvar+':', coordinates
                
            extra['coordinates'] = coordinates
    
        # Grid mapping
        if grid_mapping:
            grid_mapping = ' '.join(grid_mapping)
            if _debug:
                print '    Writing grid_mapping to netCDF variable', ncvar+':', grid_mapping
                
            extra['grid_mapping'] = grid_mapping
    
        # Ancillary variables
        if ancillary_variables:
            ancillary_variables = ' '.join(ancillary_variables)
            if _debug:
                print '    Writing ancillary_variables to netCDF variable', ncvar+':', ancillary_variables

            extra['ancillary_variables'] = ancillary_variables
            
#        # Flag values
#        if hasattr(f, 'flag_values'):
#            extra['flag_values'] = f.flag_values
#    
#        # Flag masks
#        if hasattr(f, 'flag_masks'):
#            extra['flag_masks'] = f.flag_masks
#    
#        # Flag meanings
#        if hasattr(f, 'flag_meanings'):
#            extra['flag_meanings'] = f.flag_meanings
    
        # name can be a dimension of the variable, a scalar coordinate
        # variable, a valid standard name, or the word 'area'
        cell_methods = self._get_cell_methods(f)
        if cell_methods:
            axis_map = g['axis_to_ncdim'].copy()
            axis_map.update(g['axis_to_ncscalar'])

            cell_methods_strings = []
            for cm in cell_methods.values():                
                axes = [axis_map.get(axis, axis) for axis in cm.get_axes(())]
                cm.set_axes(axes)
                cell_methods_strings.append(str(cm)) # self.cell_method_string(cm)

#            cell_methods = ' '.join([str(cm.change_axes(axis_map))
#                                              for cm in cell_methods.values()])
            cell_methods = ' '.join(cell_methods_strings)
            if _debug:
                print '    Writing cell_methods to netCDF variable', ncvar+':', cell_methods

            extra['cell_methods'] = cell_methods
            
        # Create a new data variable
        self._write_netcdf_variable(ncvar, ncdimensions, f,
                                    omit=g['global_properties'],
                                    extra=extra)
        
        # Update the 'seen' dictionary, if required
        if add_to_seen:
            seen[id_f] = {'variable': org_f,
                          'ncvar'   : ncvar,
                          'ncdims'  : ncdimensions}
    #--- End: def


    def _get_array(self, data):
        '''
        '''
        return data.get_array()

    def _get_auxiliary_coordinates(self, field):
        '''
        '''
        return field.auxiliary_coordinates()

    def _get_bounds(self, construct, *default):
        '''
        '''
        return construct.get_bounds(*default)

    def _get_cell_measures(self, field):
        '''
        '''
        return field.cell_measures()
        
    def _get_cell_methods(self, field):
        '''
        '''
        return field.cell_methods()
        
    def _get_construct_axes(self, field, key):
        '''
        '''
        return field.construct_axes(key)
    
    def _get_constructs(self, field, axes=None):
        return field.constructs(axes=axes)

    
    def _get_data_axes(self, field):
        '''
        '''
        return field.get_data_axes()
    #--- End: def

    def _get_domain_ancillaries(self, field):
        '''
        '''
        return field.domain_ancillaries()

    def _get_domain_axes(self, field):
        '''
        '''
        return field.domain_axes()
        
    def _get_domain_axis_size(self, field, axis):
        '''
        '''
        return self._get_domain_axes(field)[axis].get_size()

                            
    def _unlimited(self, field, axis):
        '''
        '''
        g = self.write_vars

        unlimited = field.unlimited().get(axis)
    
        if unlimited is None:
            unlimited = False
            for u in g['unlimited']:
                if field.axis(u, key=True) == axis:
                    unlimited = True
                    break
        
        return unlimited
    #--- End: def
    
    def _write_global_properties(self, fields):
        '''Find the netCDF global properties from all of the input fields and
write them to the netCDF4.Dataset.
    
.. note:: This function updates ``g['global_properties']``.
    
:Parameters:
  
    fields : list
  
:Returns:
    
    `None`
        
        '''
        g = self.write_vars
        
        # Data variable properties, as defined in Appendix A, without
        # those which are not simple.
        data_properties = set(('add_offset',
                               'cell_methods',
                               '_FillValue',
                               'flag_masks',
                               'flag_meanings',
                               'flag_values',
                               'long_name',
                               'missing_value',
                               'scale_factor',
                               'standard_error_multiplier',
                               'standard_name',
                               'units',
                               'valid_max',
                               'valid_min',
                               'valid_range',
                               ))
    
        # Global properties, as defined in Appendix A
        global_properties = set(('comment',
                                 'Conventions',
                                 'featureType',
                                 'history',
                                 'institution',
                                 'references',
                                 'source',
                                 'title',
                                 ))
    
        # Put all non-standard CF properties (i.e. those not in the
        # data_properties set) into the global_properties set, but
        # omitting those which have been requested to be on variables.
        for f in fields:
#            for attr in set(f._simple_properties()) - global_properties - g['variable_attributes']:
            for attr in set(f.properties()) - global_properties - g['variable_attributes']: # DCH CHECK
                if attr not in data_properties:
                    global_properties.add(attr)
        #--- End: for
    
        # Remove properties from the new global_properties set which
        # have different values in different fields
        f0 = fields[0]
        for prop in tuple(global_properties):
            if not self.has_property(f0, prop):
                global_properties.remove(prop)
                continue
                
            prop0 = self.get_property(f0, prop)
    
            if len(fields) > 1:
                for f in fields[1:]:
                    if (not self.has_property(f, prop) or 
                        not equals(self.get_property(f, prop), prop0, traceback=False)):
                        global_properties.remove(prop)
                        break
        #--- End: for
    
        # Write the global properties to the file
        g['netcdf'].setncattr('Conventions', g['Conventions'])
        
        for attr in global_properties - set(('Conventions',)):
            g['netcdf'].setncattr(attr, self.get_property(f0, attr)) 
    
        g['global_properties'] = global_properties
    #--- End: def

    def copy_field(self, field):
        '''

:Parameters:

    field: 

:Returns:

    out:

        '''
        return field.copy()
    #--- End: def
        
    def file_close(self, filename):
        '''Close the netCDF file that has been written.

:Returns:

    `None`

        '''
        self.write_vars['netcdf'].close()
    #--- End: def

    def file_open(self, filename, mode, fmt):
        '''Open the netCDF file for writing.
        
:Returns:
        
    out: `netCDF.Dataset`
        
        '''
        try:        
            nc = netCDF4.Dataset(filename, mode, format=fmt)
        except RuntimeError as error:
            raise RuntimeError("{}: {}".format(error, filename))        
        else:
            return nc
    #--- End: def

    @classmethod
    def file_type(cls, filename):
        '''Find the format of a file.
    
:Parameters:
    
    filename: `str`
        The file name.
    
:Returns:
 
    out: `str`
        The format type of the file.
    
:Examples:

>>> filetype = n.file_type(filename)
    
    '''
        # ----------------------------------------------------------------
        # Assume that URLs are in netCDF format
        # ----------------------------------------------------------------
        if filename.startswith('http://'):
           return 'netCDF'
    
        # ----------------------------------------------------------------
        # netCDF
        # ----------------------------------------------------------------
        if netcdf.is_netcdf_file(filename):
            return 'netCDF'
    #--- End: def

    def get_coordinate_reference_coordinates(self, coordinate_reference):
        '''Return the coordinates of a coordinate reference object.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `set`

        '''
        return coordinate_reference.coordinates()
    #--- End: def

    def get_coordinate_conversion_parameters(self, coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.get_coordinate_conversion().parameters()
    #--- End: def

    def get_coordinate_references(self, field):
        '''
        '''
        return field.coordinate_references()
    #--- End: def

    def get_coordinates(self, field):
        '''
        '''
        return field.coordinates()
    #--- End: def

    def get_data(self, parent, *default):
        '''Return the data array.

:Examples 1:

>>> data = w.get_data(x)

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: 
        The data array.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_data(d)
<Data: [-89.5, ..., 89.5] degrees_north>

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_data(b)
<Data: [[-90, ..., 90]] degrees_north>
        '''
        return parent.get_data(*default)
    #--- End: def

    def get_datum(self, coordinate_reference):
        '''

:Returns:

    out: `dict`

        '''
        return coordinate_reference.get_datum()
    #--- End: def

    def get_datum_domain_ancillaries(self, coordinate_reference):
        '''Return the domain ancillary-valued terms of a coordinate reference
datum.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `dict`
        '''        
        return self.get_datum(coordinate_reference).domain_ancillaries()
    #--- End: def
        
    def get_datum_parameters(self, coordinate_reference):
        '''Return the parameter-valued terms of a coordinate reference datum.

:Parameters:

    coordinate_reference: `CoordinateReference`

:Returns:

    out: `dict`

        '''        
        return self.get_datum(coordinate_reference).parameters()
    #--- End: def

    def get_dimension_coordinates(self, field):
        '''
        '''
        return field.dimension_coordinates()
    #--- End: def

    def get_field_ancillaries(self, field):
        '''Return the field ancillaries of a field.

:Examples 1:

>>> field_ancillaries = w.get_field_ancillaries(f)

:Parameters:

    field: 
        The field object.

:Returns:

    out: `dict`
        The field ancillary objects, keyed by their internal identifiers.

:Examples 2:

>>> w.get_field_ancillaries(f)
{'fieldancillary0': <FieldAncillary: >,
 'fieldancillary1': <FieldAncillary: >}
        '''
        return field.field_ancillaries()
    #--- End: def
    
    def get_measure(self, cell_measure):
        '''Return the measure property of a cell measure contruct.

:Examples 1:

>>> measure = w.get_measure(c)

:Parameters:

    cell_measure:
        The cell measure object.

:Returns:

    out: `str` or `None`
        The measure property, or `None` if it has not been set.

:Examples 2:

>>> c
<CellMeasure: area(73, 96) km2>
>>> w.get_measure(c)
'area'
        '''
        return cell_measure.get_measure(None)
    #--- End: def
    
    def get_ncvar(self, parent, *default):
        '''Return the netCDF variable name.

:Examples 1:

>>> ncvar = w.get_ncvar(x)

:Parameters:

    parent: 
        The object containing the data array.

    default: `str`, optional

:Returns:

    out: 
        The netCDF variable name.

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_ncvar(d)
'lat'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_ncvar(b)
'lat_bnds'

>>> w.get_ncvar(x)
AttributeError: Can't get non-existent 'ncvar'
>>> w.get_ncvar(x, 'newname')
'newname'
        '''
        return parent.get_ncvar(*default)
    #--- End: def

    def get_ndim(self, parent):
        '''Return the number of dimensions spanned by the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: int
        The number of dimensions spanned by the data array.

:Examples 1:

>>> ndim = w.get_ndim(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_ndim(d)
1

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_ndim(b)
2
        '''
        return parent.ndim
    #--- End: def

    def get_properties(self, parent):
        '''Return all properties.

:Parameters:

    parent: 
        The object containing the properties.

:Returns:

    out: `dict`
        The property names and their values

:Examples 1:

>>> properties = w.get_properties(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_properties(d)
{'units: 'degrees_north'}
 'standard_name: 'latitude',
 'foo': 'bar'}
        '''
        return parent.properties()
    #--- End: def
    
    def get_property(self, parent, prop, *default):
        '''Return a property value.

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: 
        The value of the property.

:Examples 1:

>>> value = w.get_property(x, 'standard_name')

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_property(d, 'units')
'degees_north'

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_property(b, 'long_name')
'Latitude Bounds'

>>> w.get_property(x, 'foo')
AttributeError: Can't get non-existent property 'foo'
>>> w.get_property(x, 'foo', 'bar')
'bar'
        '''
        return parent.get_property(prop, *default)
    #--- End: def
    
    def get_shape(self, parent):
        '''Return the shape of the data array.

:Parameters:

    parent: 
        The object containing the data array.

:Returns:

    out: tuple
        The shape of the data array.

:Examples 1:

>>> shape = w.get_shape(x)

:Examples 2:

>>> d
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.get_shape(d)
(180,)

>>> b
<Bounds: latitude(180, 2) degrees_north>
>>> w.get_shape(b)
(180, 2)

        '''
        return parent.shape
    #--- End: def

    def has_property(self, parent, prop):
        '''Return True if a property exists.

:Examples 1:

>>> has_standard_name = w.has_property(x, 'standard_name')

:Parameters:

    parent: 
        The object containing the property.

:Returns:

    out: `bool`
        `True` if the property exists, otherwise `False`.

:Examples 2:

>>> coord
<DimensionCoordinate: latitude(180) degrees_north>
>>> w.has_property(coord, 'units')
True

>>> bounds
<Bounds: latitude(180, 2) degrees_north>
>>> w.has_property(bounds, 'long_name')
False
        '''
        return parent.has_property(prop)
    #--- End: def

    def initialise(self, class_name, **kwargs):
        '''
        '''
        return self.implementation.get_class(class_name)(**kwargs)
    #--- End: def

    def set_coordinate_reference_coordinate(self, coordinate_reference,
                                            coordinate):
        '''
        '''
        coordinate_reference.set_coordinate(coordinate)
    #--- End: def
        
    def write(self, fields, filename, fmt='NETCDF4', overwrite=True,
              verbose=False, mode='w', least_significant_digit=None,
              endian='native', compress=0, fletcher32=False,
              no_shuffle=False, datatype=None,
              variable_attributes=None, HDF_chunks=None,
              unlimited=None, extra_write_vars=None, Conventions=None,
              _debug=False):
        '''Write fields to a netCDF file.
        
NetCDF dimension and variable names will be taken from variables'
`!ncvar` attributes and the field attribute `!ncdimensions` if
present, otherwise they are inferred from standard names or set to
defaults. NetCDF names may be automatically given a numerical suffix
to avoid duplication.
    
Output netCDF file global properties are those which occur in the set
of CF global properties and non-standard data variable properties and
which have equal values across all input fields.
    
Logically identical field components are only written to the file
once, apart from when they need to fulfil both dimension coordinate
and auxiliary coordinate roles for different data variables.
    
:Parameters:

    fields : (arbitrarily nested sequence of) `cf.Field`
        The field or fields to write to the file.

    filename : str
        The output CF-netCDF file. Various type of expansion are
        applied to the file names:
        
          ====================  ======================================
          Expansion             Description
          ====================  ======================================
          Tilde                 An initial component of ``~`` or
                                ``~user`` is replaced by that *user*'s
                                home directory.
           
          Environment variable  Substrings of the form ``$name`` or
                                ``${name}`` are replaced by the value
                                of environment variable *name*.
          ====================  ======================================
    
        Where more than one type of expansion is used in the same
        string, they are applied in the order given in the above
        table.

          Example: If the environment variable *MYSELF* has been set
          to the "david", then ``'~$MYSELF/out.nc'`` is equivalent to
          ``'~david/out.nc'``.
  
    fmt : str, optional
        The format of the output file. One of:

           =====================  ================================================
           fmt                    Description
           =====================  ================================================
           ``'NETCDF3_CLASSIC'``  Output to a CF-netCDF3 classic format file
           ``'NETCDF3_64BIT'``    Output to a CF-netCDF3 64-bit offset format file
           ``'NETCDF4_CLASSIC'``  Output to a CF-netCDF4 classic format file
           ``'NETCDF4'``          Output to a CF-netCDF4 format file
           =====================  ================================================

        By default the *fmt* is ``'NETCDF3_CLASSIC'``. Note that the
        netCDF3 formats may be slower than any of the other options.

    overwrite: bool, optional
        If False then raise an exception if the output file
        pre-exists. By default a pre-existing output file is over
        written.

    verbose : bool, optional
        If True then print one-line summaries of each field written.

    mode : str, optional
        Specify the mode of write access for the output file. One of:
 
           =======  ==================================================
           mode     Description
           =======  ==================================================
           ``'w'``  Create the file. If it already exists and
                    *overwrite* is True then the file is deleted prior
                    to being recreated.
           =======  ==================================================
       
        By default the file is opened with write access mode ``'w'``.
    
    datatype : dict, optional
        Specify data type conversions to be applied prior to writing
        data to disk. Arrays with data types which are not specified
        remain unchanged. By default, array data types are preserved
        with the exception of booleans (``numpy.dtype(bool)``, which
        are converted to 32 bit integers.

          **Example:**
            To convert 64 bit floats and integers to their 32 bit
            counterparts: ``dtype={numpy.dtype(float):
            numpy.dtype('float32'), numpy.dtype(int):
            numpy.dtype('int32')}``.

:Returns:

    `None`

:Examples 2:

>>> f
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
>>> write(f, 'file')

>>> type(f)
<class 'cf.field.FieldList'>
>>> type(g)
<class 'cf.field.Field'>
>>> cf.write([f, g], 'file.nc', verbose=True)
[<CF Field: air_pressure(30, 24)>,
 <CF Field: u_compnt_of_wind(19, 29, 24)>,
 <CF Field: v_compnt_of_wind(19, 29, 24)>,
 <CF Field: potential_temperature(19, 30, 24)>]
        '''    
        if _debug:
            print 'Writing to netCDF:'

        # ------------------------------------------------------------
        # Initialize dictionary of useful global variables
        # ------------------------------------------------------------
                # ------------------------------------------------------------
        # Initialise netCDF write parameters
        # ------------------------------------------------------------
        self.write_vars = {
            # CF conventions for output file
            'Conventions': Conventions,
            # Format of output file
            'fmt': None,
            # netCDF4.Dataset instance
            'netcdf'           : None,    
            # Map netCDF variable names to netCDF4.Variable instances
            'nc': {},      
            # Map netCDF dimension names to netCDF dimension sizes
            'ncdim_to_size': {},
            # Dictionary of netCDF variable names and netCDF
            # dimensions keyed by items of the field (such as a
            # coordinate or a coordinate reference)
            'seen': {},
            # Set of all netCDF dimension and netCDF variable names.
            'ncvar_names': set(()),
            # Set of global or non-standard CF properties which have
            # identical values across all input fields.
            'global_properties': set(()), 
            'variable_attributes': set(()),
            'bounds': {},
            # Compression/endian
            'compression': {},
            'endian': 'native',
            'least_significant_digit': None,
            # CF properties which need not be set on bounds if they're set
            # on the parent coordinate
            'omit_bounds_properties': ('units', 'standard_name', 'axis',
                                       'positive', 'calendar', 'month_lengths',
                                       'leap_year', 'leap_month'),
            # Data type conversions to be applied prior to writing
            'datatype': {},
            #
            'unlimited': (),
            # Print statements
            'verbose': False,
            '_debug' : False,
        }
        g = self.write_vars
        
        if extra_write_vars:
            g.update(copy.deepcopy(extra_write_vars))

        compress = int(compress)
        zlib = bool(compress) 
    
        if fmt not in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT',
                       'NETCDF4', 'NETCDF4_CLASSIC'):
            raise ValueError("Unknown output file format: {}".format(fmt))
    
        if compress and fmt in ('NETCDF3_CLASSIC', 'NETCDF3_64BIT'):
            raise ValueError("Can't compress {} format file".format(fmt))
        
        # ------------------------------------------------------------
        # Set up non-global attributes
        # ------------------------------------------------------------
        if variable_attributes:
            if isinstance(variable_attributes, basestring):
                variable_attributes = set((variable_attributes,))
            else:
                variable_attributes = set(variable_attributes)

            g['variable_attributes'] = variable_attributes
        #--- End: def
    
        # ------------------------------------------------------------
        # Set up data type conversions. By default, booleans are
        # converted to 32-bit integers and python objects are
        # converted to 64-bit floats.
        # ------------------------------------------------------------
        dtype_conversions = {numpy.dtype(bool)  : numpy.dtype('int32'),
                             numpy.dtype(object): numpy.dtype(float)}
        if datatype:
            dtype_conversions.update(datatype)

        g['datatype'].update(dtype_conversions)

        if unlimited:
            g['unlimited'] = unlimited
    
        # -------------------------------------------------------
        # Compression/endian
        # -------------------------------------------------------
        g['compression'].update(
            {'zlib'       : zlib,
             'complevel'  : compress,
             'fletcher32' : fletcher32,
             'shuffle'    : not no_shuffle,
            })
        g['endian'] = endian
        g['least_significant_digit'] = least_significant_digit
        
        g['verbose'] = verbose
        g['_debug']  = _debug        
        
        g['fmt'] = fmt
    
        # ---------------------------------------------------------------
        # Flatten the sequence of intput fields
        # ---------------------------------------------------------------
        fields = list(flat(fields))
    
        # ---------------------------------------------------------------
        # Still here? Open the output netCDF file.
        # ---------------------------------------------------------------
    #    if mode != 'w':
    #        raise ValueError("Can only set mode='w' at the moment")
    
        filename = os.path.expanduser(os.path.expandvars(filename))
        
        if mode == 'w' and os.path.isfile(filename):
            if not overwrite:
                raise IOError(
                    "Can't write to an existing file unless overwrite=True: {}".format(
                        abspath(filename)))
                    
            if not os.access(filename, os.W_OK):
                raise IOError(
                    "Can't overwrite an existing file without permission: {}".format(
                        abspath(filename)))
                
            os.remove(filename)
        #--- End: if          

        # ------------------------------------------------------------
        # Open the netCDF file to be written
        # ------------------------------------------------------------
        g['filename'] = filename
        g['netcdf'] = self.file_open(filename, mode, fmt)
    
        # ---------------------------------------------------------------
        # Set the fill mode for a Dataset open for writing to off. This
        # will prevent the data from being pre-filled with fill values,
        # which may result in some performance improvements.
        # ---------------------------------------------------------------
        g['netcdf'].set_fill_off()
    
        # ---------------------------------------------------------------
        # Write global properties to the file first. This is important as
        # doing it later could slow things down enormously. This function
        # also creates the g['global_properties'] set, which is used in
        # the _write_field function.
        # ---------------------------------------------------------------
        self._write_global_properties(fields)
    
        # ---------------------------------------------------------------
        #
        # ---------------------------------------------------------------
        for f in fields:
    
    #        # Set HDF chunking
    #        chunks = f.HDF_chunks()
    #        if chunks
    #        
    #        org_chunks = f.HDF_chunks(HDF_chunks)
    #        default_chunks = f.HDF_chunks()
    #        chunks = org_chunks.copy()
    #        shape = f.shape
    #        for i, size in org_chunks.iteritems():
    #            if size is None:
    #                size = default_chunks[i]
    #            dim_size = shape[i]
    #            if size is None or size > dim_size:
    #                size = dim_size
    #            chunks[i] = size
    #        #--- End: for
    #        f.HDF_chunks(chunks)
    
            if g['_debug']:            
                print '  HDF chunks :', 'PASS FOR NOW' #f.HDF_chunks()
            
            # Write the field
            self._write_field(f)
    
    #        # Reset HDF chunking
    #        f.HDF_chunks(org_chunks)
        #-- End: for
    
        # ---------------------------------------------------------------
        # Write all of the buffered data to disk
        # ---------------------------------------------------------------
        self.file_close(filename)
    #--- End: def
   
#--- End: class