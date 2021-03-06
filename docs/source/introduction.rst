.. currentmodule:: cfdm
.. default-role:: obj

.. raw:: html

    <style> .small {font-size:small} </style>

.. role:: small

**Introduction**
================

----

Version |release| for version |version| of the CF conventions.

.. contents::
   :local:
   :backlinks: entry

The Python cfdm package is a reference implementation of the
:ref:`CF-data-model`.

The CF data model is a complete representation of the CF (Climate and
Forecast) metadata conventions (http://cfconventions.org) for storing
geoscientific datasets. It can describe any conceivable CF-compliant
dataset. Therefore cfdm, a software implementation of the CF
data model, will also be able to process any CF-compliant dataset.

The cfdm package is, however, not strict about CF-compliance, so that
non-conformant datasets may be created or ingested from existing
datasets and written to new datasets. This is so that existing
datasets which are non-CF-compliant may be processed by cfdm, ideally
being modified in memory to be (more) CF-compliant.

----
    
**Functionality**
-----------------

The cdfm library can create field constructs ab initio, or read them
from netCDF files, inspect, subspace and modify in memory, and write
them to CF-netCDF dataset files. As long as it can interpret the data,
cfdm does not enforce CF-compliance, allowing non-compliant datasets
to be read, processed, corrected and rewritten.

It does not contain higher-level analysis functions (such as
regidding) because the expectation is that other libraries will build
on cfdm, inheriting its comprehensive knowledge of the CF conventions,
to add more sophisticated methods.

For more details see *cfdm: A Python reference implementation of the
CF data model* in the Journal of Open Source Software:
https://doi.org/10.21105/joss.02717

.. code-block:: python
   :caption: *A simple example of reading a field construct from a
             file and inspecting it.*

   >>> import cfdm
   >>> f = cfdm.read('file.nc')
   >>> f
   [<Field: air_temperature(time(12), latitude(64), longitude(128)) K>]
   >>> print(f[0])
   Field: air_temperature (ncvar%tas)
   ----------------------------------
   Data            : air_temperature(time(12), latitude(64), longitude(128)) K
   Cell methods    : time(12): mean (interval: 1.0 month)
   Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                   : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                   : longitude(128) = [0.0, ..., 357.1875] degrees_east
                   : height(1) = [2.0] m

The cfdm package can

* read :term:`field constructs <field construct>` from netCDF and CDL
  datasets,

* create new field constructs in memory,

* write field constructs to netCDF datasets on disk,

* read, write, and create coordinates defined by geometry cells,

* read and write netCDF4 string data-type variables,

* read, write, and create netCDF and CDL datasets containing
  hierarchical groups,

* inspect field constructs,

* test whether two field constructs are the same,

* modify field construct metadata and data,

* create subspaces of field constructs,

* incorporate, and create, metadata stored in external files, and

* read, write, and create data that have been compressed by convention
  (i.e. ragged or gathered arrays), whilst presenting a view of the
  data in its uncompressed form.

Note that the cfdm package enables the representation and creation of
CF field constructs, but it is largely :ref:`up to the user to use
them in a CF-compliant way <CF-conventions>`.

A command line tool is provided that allows inspection of datasets
outside of a Python environment:

.. code-block:: console
   :caption: *Inspect a dataset from the command line.*

   $ cfdump file.nc
   Field: air_temperature (ncvar%tas)
   ----------------------------------
   Data            : air_temperature(time(12), latitude(64), longitude(128)) K
   Cell methods    : time(12): mean (interval: 1.0 month)
   Dimension coords: time(12) = [0450-11-16 00:00:00, ..., 0451-10-16 12:00:00] noleap
                   : latitude(64) = [-87.8638, ..., 87.8638] degrees_north
                   : longitude(128) = [0.0, ..., 357.1875] degrees_east
                   : height(1) = [2.0] m

**Related packages**
--------------------

The `cf-python <https://ncas-cms.github.io/cf-python>`_ package, which
is built as an extension to cfdm, includes higher-level functionality,
such as regridding, and statistical operations. In turn, the `cf-plot
<http://ajheaps.github.io/cf-plot/>`_ package provides comprehensive
visualisation of field constructs created by cf-python.

**Citation**
------------

If you use cfdm, either as a stand-alone application or to provide a
CF data model implementation to another software library, please
consider including the reference:

*Hassell et al., (2020). cfdm: A Python reference implementation of
the CF data model. Journal of Open Source Software, 5(54), 2717,
https://doi.org/10.21105/joss.02717*

.. code-block:: bibtex
   
   @article{Hassell2020,
     doi = {10.21105/joss.02717},
     url = {https://doi.org/10.21105/joss.02717},
     year = {2020},
     publisher = {The Open Journal},
     volume = {5},
     number = {54},
     pages = {2717},
     author = {David Hassell and Sadie L. Bartholomew},
     title = {cfdm: A Python reference implementation of the CF data model},
     journal = {Journal of Open Source Software}
   }

