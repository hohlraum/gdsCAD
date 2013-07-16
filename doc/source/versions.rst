***************
gdsCAD Versions
***************


v0.3.0
======
A major change that breaks backwards compatibility for element creation

* ``layer`` is no longer the leading and required parameter for geometry.
  Layer now now defaults to value of ``core.default_layer``
* Introduced ``core.default_datatype`` to specify default datatype
* bufix: fixed absent final segment in Polyline

v0.2.3
======
* Initial release