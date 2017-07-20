from __future__ import unicode_literals
import re
import semantic_version


class InvalidSemverError(ValueError):
    pass


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
            except InvalidSemverError:
                continue  # skip invalid semver strings
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
    MAJOR = 0
    MINOR = 1
    PATCH = 2
    YES = 'Y'
    LOCK = 'L'

    re_specitemmask = re.compile(r'^(<|<=||=|==|>=|>|!=|\^|~|~=)([0-9LY].*)$')

    def __init__(self, specitemmask, current_version=None):
        self.specitemmask = specitemmask
        self.current_version = _parse_semver(current_version) if current_version else None

        self.has_yes = False
        self.yes_ver = None
        self.has_lock = False
        self.kind, self.version = self.parse(specitemmask)
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
        if self.LOCK in version:
            self.has_lock = True

        if self.has_lock and not self.current_version:
            raise ValueError('Without a current_version, SpecItemMask objects with LOCKs cannot be converted to Specs')

        if self.has_lock:

            # Use _parse_semver but temporarily replace L and Y to be valid
            # this is a bit hacky...
            lock_placeholder = '9999990'
            yes_placeholder = '9999991'
            parseable_version = version.replace(self.LOCK, lock_placeholder).replace(self.YES, yes_placeholder)
            v = _parse_semver(str(parseable_version))

            # Substitute the current version integers for LOCKs
            if v.major == int(lock_placeholder):
                v.major = self.current_version.major
            if v.minor == int(lock_placeholder):
                v.minor = self.current_version.minor
            if v.patch == int(lock_placeholder):
                v.patch = self.current_version.patch
            if v.prerelease and v.prerelease[0] == lock_placeholder:
                # prerelease is a tuple of strings
                v.prerelease = self.current_version.prerelease

            # put it back into a string as expected, with L replaced and Y intact
            version = str(v).replace(yes_placeholder, self.YES)

        if self.YES in version:
            self.has_yes = True
            self.yes_ver = YesVersion(version)

        if self.has_yes:
            kind = '*'
            version = ''

        return kind, version

    def match(self, version):
        spec_match = version in self.spec
        if not self.has_yes:
            return spec_match
        else:
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
        self.specs = None
        self.op = None
        self.parse(specmask)

    def parse(self, specmask):
        if self.OR in specmask and self.AND in specmask:
            raise ValueError('SpecMask cannot contain both {} and {} operators'.format(self.OR, self.AND))

        if self.OR in specmask:
            self.op = self.OR
            self.specs = [x.strip() for x in specmask.split(self.OR)]
        elif self.AND in specmask:
            self.op = self.AND
            self.specs = [x.strip() for x in specmask.split(self.AND)]
        else:
            self.op = self.AND
            self.specs = [specmask.strip(), ]

        self.specs = [SpecItemMask(s, self.current_version) for s in self.specs]

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

    def __contains__(self, item):
        return self.match(item)

    def __eq__(self, other):
        if not isinstance(other, SpecMask):
            return NotImplemented

        return set(self.specs) == set(other.specs)

    def __str__(self):
        return "SpecMask <{}".format(self.op.join(self.specs))


class YesVersion(object):
    YES = 'Y'
    re_num = re.compile(r'^[0-9]+|Y$')

    def __init__(self, version_str):
        self.major, self.minor, self.patch, self.prerelease = None, None, None, None
        self.parse(version_str)

    def parse(self, version_str):
        """Parse a version_str into components"""

        if '-' in version_str:
            # if it looks like we have a prerelease, break it off and
            # save it first, then process the rest
            parts = version_str.split('-')
            version_str = parts[0]

            # prerelease is expected as tuple of strings split by .
            self.prerelease = tuple(parts[1].split('.')) if '.' in parts[1] else (parts[1],)

        components = version_str.split('.')
        for part in components:
            num_match = self.re_num.match(part)
            if not num_match:
                raise ValueError('YesVersion components are expected to be an integer or the character "Y",'
                                 'not: {}'.format(version_str))

            if self.major is None:
                self.major = self._int_or_y(part)
                continue

            if self.minor is None:
                self.minor = self._int_or_y(part)
                continue

            if self.patch is None:
                self.patch = self._int_or_y(part)
                continue

            # if we ever get here we've gotten too many components
            raise ValueError('YesVersion received an invalid version string: {}'.format(version_str))

    def _int_or_y(self, s):
        try:
            ret = int(s)
        except ValueError:
            ret = self.YES
        return ret

    def match(self, version):
        """version matches if all non-YES fields are the same integer number, YES fields match any integer"""
        version = _parse_semver(version)

        if self.major:
            major_valid = self.major == version.major if self.major != self.YES else True
        else:
            major_valid = 0 == version.major

        if self.minor:
            minor_valid = self.minor == version.minor if self.minor != self.YES else True
        else:
            minor_valid = 0 == version.minor

        if self.patch:
            patch_valid = self.patch == version.patch if self.patch != self.YES else True
        else:
            patch_valid = 0 == version.patch

        if self.prerelease:
            if self.prerelease[0] == self.YES:
                # Y is always valid
                prerelease_valid = True
            elif self.prerelease == version.prerelease:
                # this prerelease matches exactly
                prerelease_valid = True
            else:
                # no match
                prerelease_valid = False
        else:
            prerelease_valid = version.prerelease is ()

        return all([major_valid, minor_valid, patch_valid, prerelease_valid])

    def __contains__(self, item):
        return self.match(item)

    def __str__(self):
        return ".".join([str(x) for x in [self.major, self.minor, self.patch] if x])


def _parse_semver(version):
    if isinstance(version, semantic_version.Version):
        return version
    if isinstance(version, str):
        # strip leading 'v' and '=' chars
        cleaned = version[1:] if version.startswith('=') or version.startswith('v') else version
        try:
            v = semantic_version.Version(cleaned)
        except ValueError:
            v = semantic_version.Version.coerce(cleaned)
            if len(v.build) > 0:
                raise InvalidSemverError('build fields should not be used')
        return v
    raise ValueError('version must be either a str or a Version object')
