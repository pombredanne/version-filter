from __future__ import unicode_literals
import re
import semantic_version


class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version=None):
        """Return a list of versions that are greater than the current version and that match the mask"""
        current = semantic_version.Version(current_version) if current_version else None
        _mask = SpecMask(mask, current)

        _versions = []
        for version in versions:
            try:
                v = semantic_version.Version(version)
            except ValueError:
                continue  # skip invalid semver strings
            _versions.append(v)
        _versions.sort()

        selected_versions = [v for v in _versions if v in _mask]

        return [str(v) for v in selected_versions]

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
        self.current_version = current_version
        if current_version and isinstance(current_version, str):
            # convert current_version to Version object
            self.current_version = semantic_version.Version(current_version)

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
            # Substitute the current version integers for LOCKs
            v_parts = version.split('.')
            if v_parts[self.MAJOR] == self.LOCK:
                v_parts[self.MAJOR] = self.current_version.major
            if v_parts[self.MINOR] == self.LOCK:
                v_parts[self.MINOR] = self.current_version.minor
            if v_parts[self.PATCH] == self.LOCK:
                v_parts[self.PATCH] = self.current_version.patch
            version = '.'.join([str(x) for x in v_parts])

        if self.YES in version:
            self.has_yes = True
            v_parts = version.split('.')
            self.yes_ver = YesVersion(major=v_parts[0], minor=v_parts[1], patch=v_parts[2])

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
        if isinstance(version, str):
            v = semantic_version.Version(version)
        elif isinstance(version, semantic_version.Version):
            v = version
        else:
            raise ValueError('version must be either a str or a Version object')

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
    re_num = re.compile('^([0-9]+|Y)$')

    def __init__(self, major=None, minor=None, patch=None):
        if not all([self.re_num.match(major), self.re_num.match(minor), self.re_num.match(patch)]):
            raise ValueError('all parameters are expected to be integers or the character "Y"')

        try:
            self.major = int(major)
        except ValueError:
            self.major = self.YES

        try:
            self.minor = int(minor)
        except ValueError:
            self.minor = self.YES

        try:
            self.patch = int(patch)
        except ValueError:
            self.patch = self.YES

    def match(self, version):
        """version matches if all non-YES fields are the same integer number, YES fields match any integer"""
        if isinstance(version, str):
            version = semantic_version.Version(version)

        major_valid = self.major == version.major if self.major != self.YES else True
        minor_valid = self.minor == version.minor if self.minor != self.YES else True
        patch_valid = self.patch == version.patch if self.patch != self.YES else True

        return all([major_valid, minor_valid, patch_valid])

    def __contains__(self, item):
        return self.match(item)

    def __str__(self):
        return "({}, {}, {})".format(self.major, self.minor, self.patch)
