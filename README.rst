Introduction
==========================

updatedir is a python module which pushes updates from one directory to another.
It is intended to automatically handle the transport layer.

As of 0.1, only local update and update over ssh are supported.

The update algorithm is also rather stupid - it just skips any files if the filename
already exists. This could be made more sophisiticated, but is beyond my current needs.


Credits
-------

- `Paramiko`_
- `Distribute`_
- `Buildout`_
- `modern-package-template`_

.. _Paramiko: http://www.lag.net/paramiko/
.. _Buildout: http://www.buildout.org/
.. _Distribute: http://pypi.python.org/pypi/distribute
.. _`modern-package-template`: http://pypi.python.org/pypi/modern-package-template
