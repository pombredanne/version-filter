from __future__ import unicode_literals
import re
import semantic_version


class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version=None):
        """Return a list of versions that are greater than the current version and that match the mask"""
        current = parse_semver(current_version) if current_version else None
        _mask = SpecMask(mask, current)

        _versions = []
        for version in versions:
            try:
                v = parse_semver(version)
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
    MAJOR = 0
    MINOR = 1
    PATCH = 2
    YES = 'Y'
    LOCK = 'L'

    re_specitemmask = re.compile(r'^(<|<=||=|==|>=|>|!=|\^|~|~=)([0-9LY].*)$')

    def __init__(self, specitemmask, current_version=None):
        self.specitemmask = specitemmask
        self.current_version = parse_semver(current_version) if current_version else None

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
            v_parts = (version.split('.') + [None, None, None])[0:3]  # make sure we have three items, 'None' padded
            if v_parts[self.MAJOR] == self.LOCK:
                v_parts[self.MAJOR] = self.current_version.major
            if v_parts[self.MINOR] == self.LOCK:
                v_parts[self.MINOR] = self.current_version.minor
            if v_parts[self.PATCH] == self.LOCK:
                v_parts[self.PATCH] = self.current_version.patch
            version = '.'.join([str(x) for x in v_parts if x])

        if self.YES in version:
            self.has_yes = True
            v_parts = (version.split('.') + [None, None, None])[0:3]  # make sure we have three items, 'None' padded
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
        v = parse_semver(version)

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
        self.major, self.minor, self.patch = None, None, None

        if major is not None and not self.re_num.match(major):
            raise ValueError('the major parameter is expected to be an integer or the character "Y"')
        if minor is not None and not self.re_num.match(minor):
            raise ValueError('the minor parameter is expected to be an integer or the character "Y"')
        if patch is not None and not self.re_num.match(patch):
            raise ValueError('the patch parameter is expected to be an integer or the character "Y"')

        if major:
            try:
                self.major = int(major)
            except ValueError:
                self.major = self.YES

        if minor:
            try:
                self.minor = int(minor)
            except ValueError:
                self.minor = self.YES

        if patch:
            try:
                self.patch = int(patch)
            except ValueError:
                self.patch = self.YES

    def match(self, version):
        """version matches if all non-YES fields are the same integer number, YES fields match any integer"""
        version = parse_semver(version)

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

        return all([major_valid, minor_valid, patch_valid])

    def __contains__(self, item):
        return self.match(item)

    def __str__(self):
        return ".".join([str(x) for x in [self.major, self.minor, self.patch] if x])


def parse_semver(version):
    if isinstance(version, semantic_version.Version):
        return version
    if isinstance(version, str):
        return semantic_version.Version.coerce(version)
    raise ValueError('version must be either a str or a Version object')
