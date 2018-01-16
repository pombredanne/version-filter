==============
version-filter
==============


.. image:: https://travis-ci.org/dropseedlabs/version-filter.svg?branch=master
        :target: https://travis-ci.org/dropseedlabs/version-filter

.. image:: https://img.shields.io/pypi/v/version_filter.svg
        :target: https://pypi.python.org/pypi/version_filter

.. image:: https://img.shields.io/pypi/l/version_filter.svg
        :target: https://pypi.python.org/pypi/version_filter

.. image:: https://img.shields.io/pypi/pyversions/version_filter.svg
        :target: https://pypi.python.org/pypi/version_filter


A semantic and regex version filtering/masking library.

Given a filtering mask or regex and a list of versions (as strings), a subset of that list of versions will be returned.
If a mask is given and the mask uses current version references, an explicit current version must also be provided as an
imput must also be provided as an imput.

Inputs
------

Mask/Regex
~~~~~~~~~~

The Mask can be a SemVer v2 valid mask with the following extensions.

Mask Lock Extension
...................

Locks (``L``) are used as a substitution character in the mask for the major, minor and patch components where you want
to limit the version filter to just those versions where it has the same value as the given current_version.  If a ``L``
is present anywhere in the mask, a current_version parameter must also be provided.  By giving a positive integer
immediately following the 'L' you can express "lock + int" behavior.  For example, ``L1`` in a mask states "the current
version number + 1" for any given position.

Mask Yes Extension
..................

Yes (``Y``) are used to provide wildcard acceptance of any value in the position of the ``Y``.  It can be used in the
major, minor, patch or pre-release components of version'

'Next Best' Matching Extension
...............................

Some packages fail to ever publicly release expected semantic versions.  Take for instance a package that never releases
a ``'2.0.0'`` version, but instead has ``'2.0.1'`` as the first available version of the 2 series.  To be able to handle
that convention deviation without resorting to ranges or wildcards and thus losing some of the power of the Lock and Yes
extensions you can prefix a mask with the hyphen (``-``) character.  This allows the algorithm to anticipate what
releases "should" get released, and select the "next" release if the anticipated release never appears.  For instance,
the mask ``'-Y.0.0'`` anticipates that the ``'2.0.0'`` release will be made, but will return the ``2.0.1`` if the
``2.0.0`` release never appears.

Boolean AND and OR
..................

Boolean AND operators (``&&``) and boolean OR operators (``||``) can be used to combine masks.  However, both AND and OR
*cannot* be combined in the same expression.

Mask Examples
.............

Some common examples:

* ``'1.Y.0'`` # return only those minor versions that are of major release 1
* ``'L.Y.0'`` # return only those minor versions that are greater than the currently installed version, but in the same
  major release
* ``'>=L1.0.0'`` # return every version for major versions at least 1 greater that the current major version
* ``'-Y.0.0'`` # return only major versions that are greater than the currently installed version with "next best"
  matching enabled (will return a 2.0.1 release if 2.0.0 is never released)
* ``'L.L.Y'`` # return only those patch versions that are greater than the currently installed version, but in the same
  major and minor release
* ``'Y.Y.Y'`` # return all major, minor and patch versions
* ``'Y.Y.Y-Y'`` # return all major, minor, patch and prerelease versions
* ``'L.L.Y || Y.Y.0'`` # return patch versions of my currently installed version or all major and minor releases
* ``'>1.0.0 && <3.0.0'`` # return all versions between 1.0.0 and 3.0.0, exclusive
* ``'*'`` # return all versions, including pre-releases

List of version strings
~~~~~~~~~~~~~~~~~~~~~~~

The list of version strings is expected to be a set of well formed semantic versions conforming to the SemVer v2 spec.

Current Version
~~~~~~~~~~~~~~~

A version string that conforms to the SemVer v2 spec.

Usage
-----

.. code-block:: python

    from version_filter import VersionFilter

    mask = 'L.Y.Y'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', 'nightly']
    current_version = '1.9.0'

    VersionFilter.semver_filter(mask, versions, current_version)
    # ['1.9.1', '1.10.0']

    VersionFilter.regex_filter(r'^night', versions)
    # ['nightly']

Resources
---------

* `Semver Specification <http://semver.org//>`_
* `NPM Semver Spec <https://semver.npmjs.com/>`_
* `Yarn <https://yarnpkg.com/lang/en/docs/dependency-versions/>`_
* `Dependencies.io Docs <http://dependencies-public.netlify.com/docs/>`_

License
-------
* Free software: MIT license

Credits
-------
* Paul Ortman
* Dave Gaeddert
