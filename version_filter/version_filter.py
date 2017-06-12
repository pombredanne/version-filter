from __future__ import unicode_literals
import re
import semantic_version


_LOCK = 'L'
_YES = 'Y'
_MAJOR = 0
_MINOR = 1
_PATCH = 2

class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version=None):
        """Return a list of versions that are greater than the current version and that match the mask"""
        current = _parse_semver(current_version) if current_version else None
        _mask = SpecMask(mask, current)

        _versions = []
        for version in versions:
            try:
                v = _parse_semver(version)
                v.original_string = version
            except ValueError:
                continue  # skip invalid semver strings
            _versions.append(v)
        _versions.sort()

        selected_versions = [v for v in _versions if v in _mask]

        return [v.original_string for v in selected_versions]

    @staticmethod
    def regex_filter(regex_str, versions):
        """Return a list of versions that match the given regular expression."""
        regex = re.compile(regex_str)
        return [v for v in versions if regex.search(v)]


class SpecItemMask(object):
    re_specitemmask = re.compile(r'^(<|<=||=|==|>=|>|!=|\^|~|~=)([0-9LY].*)$')

    def __init__(self, specitemmask, current_version=None):
        self.specitemmask = specitemmask
        self.current_version = _parse_semver(current_version) if current_version else None

        self.has_yes = False
        self.yes_ver = None
        self.has_lock = False
        self.kind, self.version = self.parse(specitemmask)
        self.version = self.substitute(self.version, self.current_version)
        self.spec = self.get_spec()

    def __unicode__(self):
        return "SpecItemMask <{} -> >"

    def parse(self, specitemmask):
        if '*' in specitemmask:
            return '*', ''

        match = self.re_specitemmask.match(specitemmask)
        if not match:
            raise ValueError('Invalid SpecItemMask: "{}"'.format(specitemmask))

        kind, version = match.groups()
        if _LOCK in version:
            self.has_lock = True

        if _YES in version:
            self.has_yes = True
            self.yes_ver = YesVersion(version)

        if self.has_yes:
            kind = '*'
            version = ''

        return kind, version

    def substitute(self, version, current_version):
        if self.has_lock and not current_version:
            raise ValueError('Without a current_version, SpecItemMask objects with LOCKs cannot be converted to Specs')

        if self.has_lock:
            version = _substitute_current_version(version, self.current_version)

        return version

    @classmethod
    def is_valid(cls, specitemmask):
        try:
            cls.parse(specitemmask)
        except:
            return False

        return True

    def match(self, version):
        spec_match = version in self.spec
        if not self.has_yes:
            return spec_match
        else:
            if self.has_lock:
                assert self.current_version
                self.yes_ver.substitute(self.current_version)

            return spec_match and version in self.yes_ver

    def __contains__(self, item):
        return self.match(item)

    def get_spec(self):
        return semantic_version.Spec("{}{}".format(self.kind, self.version))


class SpecMask(object):
    AND = "&&"
    OR = "||"

    def __init__(self, specmask, current_version=None):
        self.speckmask = specmask
        self.current_version = current_version
        self.op = None
        self.specs = self.itemparse(self.parse(specmask))

    def parse(self, specmask):
        if self.OR in specmask and self.AND in specmask:
            raise ValueError('SpecMask cannot contain both {} and {} operators'.format(self.OR, self.AND))

        if self.OR in specmask:
            self.op = self.OR
            specs = [x.strip() for x in specmask.split(self.OR)]
        elif self.AND in specmask:
            self.op = self.AND
            specs = [x.strip() for x in specmask.split(self.AND)]
        else:
            self.op = self.AND
            specs = [specmask.strip(), ]

        return specs

    def itemparse(self, specs):
        specs = [SpecItemMask(s, self.current_version) for s in specs]
        return specs

    @classmethod
    def itemvalidate(cls, specs):
        specs = [SpecItemMask.is_valid(s) for s in specs]
        return all(specs)

    def match(self, version):
        v = _parse_semver(version)

        # We implicitly require that SpecMasks disregard releases older than the current_version if it is specified
        if self.current_version:
            newer_than_current = semantic_version.Spec('>{}'.format(self.current_version))
        else:
            newer_than_current = semantic_version.Spec('*')

        if self.op == self.AND:
            return all([v in x for x in self.specs]) and v in newer_than_current
        else:
            return any([v in x for x in self.specs]) and v in newer_than_current

    @classmethod
    def is_valid(cls, specmask):
        try:
            specs = cls.parse(specmask)
        except ValueError:
            return False
        if cls.itemparse(specs):
            return True
        return False

    def __contains__(self, item):
        return self.match(item)

    def __eq__(self, other):
        if not isinstance(other, SpecMask):
            return NotImplemented

        return set(self.specs) == set(other.specs)

    def __str__(self):
        return "SpecMask <{}".format(self.op.join(self.specs))


class YesVersion(object):
    re_prerelease_part = re.compile(r'^([0-9]+|Y|L)-(.*)$')
    re_num = re.compile(r'^[0-9]+|Y|L$')

    def __init__(self, version_str):
        self.major, self.minor, self.patch, self.prerelease = None, None, None, None
        self.parse(version_str)

    def parse(self, version_str):
        """Parse a version_str into components"""

        components = version_str.split('.')
        for part in components:

            prerelease_match = self.re_prerelease_part.match(part)
            # if any of the components looks like a pre-release component ...
            if prerelease_match:
                self.patch, self.prerelease = prerelease_match.groups()
                continue

            num_match = self.re_num.match(part)
            if not num_match:
                raise ValueError('YesVersion components are expected to be an integer or the character "Y",'
                                 'not: {}'.format(version_str))

            if self.major is None:
                self.major = self._safe_value(part)
                continue

            if self.minor is None:
                self.minor = self._safe_value(part)
                continue

            if self.patch is None:
                self.patch = self._safe_value(part)
                continue

            # if we ever get here we've gotten too many components
            raise ValueError('YesVersion received an invalid version string: {}'.format(version_str))

    def substitute(self, current_version):
        version_str = str(self)
        version_str = _substitute_current_version(version_str, current_version)
        self.major, self.minor, self.patch, self.prerelease = None, None, None, None
        self.parse(version_str)

    def _safe_value(self, s):
        if s == _YES:
            return _YES
        if s == _LOCK:
            return _LOCK
        try:
            ret = int(s)
        except ValueError:
            raise
        return ret

    def match(self, version):
        """version matches if all non-YES fields are the same integer number, YES fields match any integer"""
        version = _parse_semver(version)

        if self.major:
            major_valid = self.major == version.major if self.major != _YES else True
        else:
            major_valid = 0 == version.major

        if self.minor:
            minor_valid = self.minor == version.minor if self.minor != _YES else True
        else:
            minor_valid = 0 == version.minor

        if self.patch:
            patch_valid = self.patch == version.patch if self.patch != _YES else True
        else:
            patch_valid = 0 == version.patch

        if self.prerelease:
            if self.prerelease == _YES:
                prerelease_valid = True
            else:
                # version.prerelease is a tuple of subcomponents, check to make sure they are all present in our string
                if all([x in self.prerelease for x in version.prerelease]):
                    prerelease_valid = True
                else:
                    prerelease_valid = False
        else:
            prerelease_valid = version.prerelease is ()

        return all([major_valid, minor_valid, patch_valid, prerelease_valid])

    def __contains__(self, item):
        return self.match(item)

    def __str__(self):
        v = ".".join([str(x) for x in [self.major, self.minor, self.patch] if x is not None])
        v = v + '-{}'.format(self.prerelease) if self.prerelease is not None else v

        return v


def _parse_semver(version):
    if isinstance(version, semantic_version.Version):
        return version
    if isinstance(version, str):
        # strip leading 'v' and '=' chars
        cleaned = version[1:] if version.startswith('=') or version.startswith('v') else version
        return semantic_version.Version.coerce(cleaned)
    raise ValueError('version must be either a str or a Version object')


def _substitute_current_version(version, current_version):
    assert isinstance(current_version, semantic_version.Version)
    assert isinstance(version, str)


    # Todo: what to do about not loosing the pre-release part?

    # Substitute the current version integers for LOCKs
    v_parts = (version.split('.') + [None, None, None])[0:3]  # make sure we have three items, 'None' padded
    if v_parts[_MAJOR] == _LOCK:
        v_parts[_MAJOR] = current_version.major
    if v_parts[_MINOR] == _LOCK:
        v_parts[_MINOR] = current_version.minor
    if v_parts[_PATCH] == _LOCK:
        v_parts[_PATCH] = current_version.patch
    version = '.'.join([str(x) for x in v_parts if x is not None])

    return version
