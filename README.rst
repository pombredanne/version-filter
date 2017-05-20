==============
version-filter
==============


.. image:: https://img.shields.io/pypi/v/version_filter.svg
        :target: https://pypi.python.org/pypi/version_filter

.. image:: https://img.shields.io/travis/dropseedlabs/version_filter.svg
        :target: https://travis-ci.org/dropseedlabs/version_filter

.. image:: https://readthedocs.org/projects/version-filter/badge/?version=latest
        :target: https://version-filter.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/dropseedlabs/version_filter/shield.svg
     :target: https://pyup.io/repos/github/dropseedlabs/version_filter/
     :alt: Updates


A semantic and regex version filtering/masking library.

Given a filtering mask or regex and a list of versions (as strings), a subset of that list of versions will be returned.
If a mask is given and the mask uses current version references, an explicit current version must also be provided as an
imput must also be provided as an imput.

Inputs
---------

Mask/Regex
~~~~~~~~~~

The Mask can be a SemVer v2 valid mask with the following extensions.

Mask Lock Extension
...................

Locks (``L``) are used as a substituion character in the mask where you want to limit the version filter to just those
versions where it has the same value.  If a ``L`` is present anywhere in the mask, a current_version parameter must also
be provided.

Mask Yes Extension
..................

Yes (``Y``) are used to provide wildcard acceptance of any value in the position of the ``Y``.

Boolean AND and OR
..................

Boolean AND operators (``&&``) and boolean OR operators (``||``) can be used to combine masks.  However, both AND and OR
*cannot* be combined in the same expression.

Mask Examples
..............

Some common examples:

* ``'1.Y.0'`` # return only those minor versions that are of major release 1
* ``'L.Y.0'`` # return only those minor versions that are of the currently installed version
* ``'L.L.Y'`` # return only those patch versions that are of the currently installed version
* ``'Y.Y.Y'`` # return all major, minor and patch versions (same as '*')
* ``'L.L.Y || Y.Y.0'`` # return patch versions of my currently installed version or all major and minor releases
* ``'>1.0.0 && <3.0.0`` # return all versions between 1.0.0 and 3.0.0, exclusive

List of version strings
~~~~~~~~~~~~~~~~~~~~~~~

The list of version strings is expected to be a set of well formed semantic versions

Current Version
~~~~~~~~~~~~~~~

Usage
------

.. code-block:: python
    from version-filter import VersionFilter

    mask = 'L.Y.Y'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', 'nightly']
    current_version = '1.9.0'

    VersionFilter.semver_filter(mask, versions, current_version)
    # ['1.9.1', '1.10.0']

    VersionFilter.regex_filter(r'^night', versions)
    # ['nightly']


Resources
---------

* [NPM Semver Spec](https://semver.npmjs.com/)
* [Yarn](https://yarnpkg.com/lang/en/docs/dependency-versions/)
* [Workman Docs](http://dependencies-public.netlify.com/docs/)

License
---------
* Free software: MIT license
* Documentation: https://version-filter.readthedocs.io.

Credits
---------
* Paul Ortman
* Dave Gaeddert
