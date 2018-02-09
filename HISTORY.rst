=======
History
=======

0.7.3 (2018-02-09)
------------------

- Return the list of matched version in sorted form when doing semver filtering
- Strip _all_ leading '=' and 'v' characters from version strings


0.7.2 (2018-01-31)
------------------

- Tighten up the restrictions for '*' masks to only allow whitespace around the star


0.7.1 (2018-01-22)
------------------

- Add Semver validation method


0.7.0 (2018-01-16)
------------------

- Add support for "Last + N" matching in masks


0.6.0 (2018-01-08)
------------------

- Enable the "Next Best" matching algorithm to find next best releases when anticipated releases do not exist


0.5.1 (2017-12-09)
------------------

- Use forked version of python-semanticversion to get NPM consistent caret (^) matching behavior


0.5.0 (2017-07-19)
------------------

- Add support for pre-release locking and matching pre-releases by string


0.4.0 (2017-06-30)
------------------

- Do two-staging parsing of version strings to be more accurate and robust
- Fix a couple of documentation bugs with the package name vs project name


0.3.0 (2017-05-30)
------------------

- Accept (but ignore) version strings with leading 'v' or '=' characters


0.2.0 (2017-05-24)
------------------

- Add support for pre-release versions


0.1.1 (2017-05-23)
------------------

- Fix some documentation


0.1.0 (2017-05-20)
------------------

* First release on PyPI.
