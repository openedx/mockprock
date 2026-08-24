mockprock
=========

A simple fake implementation of a proctoring service, for development of
`edx-proctoring`_

.. _edx-proctoring: https://github.com/openedx/edx-proctoring/

Using mockprock
---------------

``mockprock`` is a development- and testing-only tool. Both the Python package
and the ``@edx/mockprock`` npm package are consumed directly from a local
checkout while developing ``edx-proctoring``.

See the `edx-proctoring developing guide`_ for the full backend setup.

.. _edx-proctoring developing guide: https://github.com/openedx/edx-proctoring/blob/master/docs/developing.rst#using-mockprock-as-a-backend

.. note::

   ``mockprock`` is **not** published to PyPI or npm. The previous npm release
   was dropped, as publishing serves no purpose for a source-consumed dev tool.