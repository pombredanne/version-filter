from __future__ import unicode_literals
from builtins import str
import re
import semantic_version


class InvalidSemverError(ValueError):
    pass


class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version=None):
        """Return a list of versions that are greater than the current version and that match the mask"""
        current = _parse_semver(current_version) if current_version else None
        specmask = SpecMask(mask, current)
        return specmask.matching_versions(versions)

    @staticmethod
    def semver_validate(mask):
        """Returns True if the given mask is valid syntactically, False otherwise"""
        try:
            specmask = SpecMask(mask, validate_only=True)
        except (InvalidSemverError, ValueError) as e:
            return False
        return True  # all mask exceptions are raised by instantiation

    @staticmethod
    def regex_filter(regex_str, versions):
        """Return a list of versions that match the given regular expression."""
        regex = re.compile(regex_str)
        return [v for v in versions if regex.search(v)]


class Component(object):
    lock_re = re.compile(r'L|L[0-9]+')
    lockint_re = re.compile(r'L([0-9]+)')
    yes_re = re.compile(r'Y')
    def __init__(self, comp):
        self.orig = comp
        self.value = 0
        self.lock = False
        self.yes = False
        match = self.lock_re.match(comp)
        if match:
            self.lock = True
            match = self.lockint_re.match(comp)
            if match:
                self.value += int(match.group(1))
            return

        if self.yes_re.match(comp):
            self.yes = True
            return

    def __str__(self):
        return '{}'.format(self.orig)

    def yesval(self):
        if self.yes:
            return str(9999991)
        return self.orig

    def lockval(self, ref):
        if self.lock:
            try:
                return str(ref + self.value)
            except TypeError:  # this can happen especially for pre-releases which can be strings
                return ref
        return self.orig


class SemverComponents(object):
    def __init__(self, major, minor, patch, other):
        self.value = 0

        self.major = Component(major) if major else ''
        self.minor = Component(minor) if minor else ''
        self.patch = Component(patch) if patch else ''
        self.other = Component(other) if other else ''

    @classmethod
    def parse(cls, version_str):

        # Try to match as much of the version string as possible.  If we can match three parts first, then two, then
        # one.  Anything we don't match is the other part.
        three_parts = re.compile(r'(([0-9LY][0-9]*)(?:\.)([0-9LY][0-9]*)(?:\.)([0-9LY][0-9]*))')
        two_parts = re.compile(r'(([0-9LY][0-9]*)(?:\.)([0-9LY][0-9]*))')
        one_part = re.compile(r'([0-9LY][0-9]*)')

        match3 = three_parts.match(version_str)
        match2 = two_parts.match(version_str)
        match1 = one_part.match(version_str)
        if match3:
            major = match3.group(2)
            minor = match3.group(3)
            patch = match3.group(4)
            other = version_str.replace(match3.group(1), '')
        elif match2:
            major = match2.group(2)
            minor = match2.group(3)
            patch = None
            other = version_str.replace(match2.group(1), '')
        elif match1:
            major = match1.group(1)
            minor = None
            patch = None
            other = version_str.replace(match1.group(1), '')
        else:
            # if nothing matched, raise an exception
            raise InvalidSemverError("{} did not contain a parseable SemVer string".format(version_str))
        other = None if other == '' else other.lstrip('-')

        return cls(major, minor, patch, other)

    def val(self):
        return self.value

    def __str__(self):
        s = '{}'.format(self.major) if self.major else ''
        s += '.{}'.format(self.minor) if self.minor else ''
        s += '.{}'.format(self.patch) if self.patch else ''
        s += '-{}'.format(self.other) if self.other else ''
        return s

    def substitute_yes(self):
        major = self.major.yesval() if self.major else None
        minor = self.minor.yesval() if self.minor else None
        patch = self.patch.yesval() if self.patch else None
        other = self.other.yesval() if self.other else None
        return SemverComponents(major, minor, patch, other)


    def substitute_lock(self, version):
        major = self.major.lockval(version.major) if self.major else None
        minor = self.minor.lockval(version.minor) if self.minor else None
        patch = self.patch.lockval(version.patch) if self.patch else None
        if self.other:
            if self.other.lock and version.prerelease:
                other = self.other.lockval('.'.join(version.prerelease))
            else:
                other = self.other.orig
        else:
            other = None

        return SemverComponents(major, minor, patch, other)


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

        self.has_next_best = False
        self.has_lock = False
        self.has_yes = False
        self.yes_ver = None

        self.kind = None
        self.version = None

        self.parse(specitemmask)  # sets kind and version attributes
        self.spec = self.get_spec()

    def __unicode__(self):
        return "SpecItemMask <{} -> >"

    def __repr__(self):
        rep = ('-' if self.has_next_best else '') + self.kind + self.version
        return "SpecItemMask <{}>".format(rep)

    def handle_yes_parsing(self):
        if self.YES in self.version:
            self.has_yes = True
            self.yes_ver = YesVersion(self.kind, self.version)

            self.kind = '*'  # Accept anything from our library spec checks, we'll special-case handle all the matching
            self.version = ''

    def handle_lock_parsing(self):
        if self.LOCK in self.version:
            self.has_lock = True

            if not self.current_version:
                raise ValueError('Without a current_version, SpecItemMask objects with LOCKs '
                                 'cannot be converted to Specs')

            mask_components = SemverComponents.parse(self.version)  # our own parsing attempt

            if not str(mask_components) == self.version:  # round trip to a string to sanity check
                raise ValueError('{} was unable to be parsed'.format(self.version))

            parseable_version = mask_components.substitute_yes().substitute_lock(self.current_version)

            # another sanity check to make sure it is a valid version string
            _parse_semver(str(parseable_version))

            # finally save the version string with locks substituted, but yeses still in the string
            self.version = str(mask_components.substitute_lock(self.current_version))

    def parse(self, specitemmask):
        if specitemmask.strip() == '*':
            self.kind = '*'
            self.version = ''
            return

        if specitemmask.startswith('-'):
            self.has_next_best = True
            specitemmask = specitemmask[1:]

        match = self.re_specitemmask.match(specitemmask)
        if not match:
            raise ValueError('Invalid SpecItemMask: "{}"'.format(specitemmask))

        self.kind, self.version = match.groups()
        self.handle_lock_parsing()
        self.handle_yes_parsing()

        if self.has_next_best and self.kind not in ['', '*']:
            raise ValueError('SpecItem {} operator kind needs to be "" or "*", was "{}". '.format(self, self.kind) +
                             'Unable to use a next_best match mode')

    def match(self, version):
        spec_match = version in self.spec and version in self.newer_than_current()
        if self.has_next_best:
            raise ValueError
        if not self.has_yes:
            return spec_match
        else:
            return spec_match and version in self.yes_ver

    def newer_than_current(self):
        if self.current_version:
            newer_than_current = semantic_version.Spec('>{}'.format(self.current_version))
        else:
            newer_than_current = semantic_version.Spec('*')

        return newer_than_current

    def matching_versions(self, versions):
        if not self.has_next_best:
            return [v for v in versions if v in self]
        else:
            return [v for v in self.next_best_matches(versions) if v in self.newer_than_current()]

    def next_best_matches(self, versions):
        if not self.has_yes:
            # specs with a lock or hard coded numbers can only result in a single fake version
            fake_version = _parse_semver(str(self.version), makefake=True)
            if fake_version not in versions:
                versions.add(fake_version)
        else:
            # versions with a YES require generating all the possible valid fake versions
            fake_versions = self.yes_ver.get_next_best_versions(versions)

            # combine fake and real versions into one set
            versions = set(versions).union(set(fake_versions))

        # For each fake version in the sorted list, get the next real version if it exists
        versions = sorted(versions)
        matched_versions = []
        for i, v in enumerate(versions):
            if hasattr(v, 'is_fake') and ((i + 1) < len(versions)):
                matched_versions.append(versions[i + 1])
        return matched_versions

    def __contains__(self, item):
        return self.match(item)

    def get_spec(self):
        return semantic_version.Spec("{}{}".format(self.kind, self.version))


class SpecMask(object):
    AND = "&&"
    OR = "||"

    def __init__(self, specmask, current_version=None, validate_only=False):
        self.speckmask = specmask
        self.validate_only = validate_only
        self.current_version = current_version
        if self.validate_only and not current_version:
            # If we're only validating, we'll make an arbitrary current version to handle masks with LOCKs
            self.current_version = '1.1.1'
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

        if self.op == self.AND:
            return all([v in x for x in self.specs])
        else:
            return any([v in x for x in self.specs])

    def matching_versions(self, versions):
        """Given a list of version, return the sorted (ascending) subset that match the mask"""
        valid_versions = set()
        for i, version in enumerate(versions):
            try:
                v = _parse_semver(version)
                valid_versions.add(v)
            except InvalidSemverError:
                continue  # skip invalid semver strings
            except ValueError:
                continue  # skip invalid semver strings

        versions_sets = []
        for s in self.specs:
            versions_sets.append(set(s.matching_versions(valid_versions)))

        matched_versions = set(versions_sets[0])  # Need to initialize with something for later intersection to work
        if self.op == self.AND:
            for v_set in versions_sets:
                matched_versions = matched_versions.intersection(v_set)
        else:
            for v_set in versions_sets:
                matched_versions = matched_versions.union(v_set)

        return [v.original_string for v in sorted(matched_versions)]

    def __contains__(self, item):
        return self.match(item)

    def __eq__(self, other):
        if not isinstance(other, SpecMask):
            return NotImplemented

        return set(self.specs) == set(other.specs)

    def __str__(self):
        return "SpecMask <{}".format(self.op.join(self.specs))


class YesVersionComponent(object):
    def __init__(self, str_val=None):
        self.component = str_val

    def __eq__(self, other):
        if not self.component:
            return 0 == other  # if uninitialized, only match against zeroes
        if self.component == YesVersion.YES:
            return True  # if it's a YES, it matches everything

        try:
            value = int(self.component)
        except ValueError:
            return False

        return value == other  # if a sucessfully parsed zero, it must be equivilant

    def val(self):
        if not self.component:
            return 0
        if self.component == YesVersion.YES:
            return None
        else:
            return int(self.component)

    @property
    def is_yes(self):
        return self.component == YesVersion.YES


class YesVersion(object):
    YES = 'Y'
    re_num = re.compile(r'^[0-9]+|Y$')

    def __init__(self, kind_str, version_str):
        self.major, self.minor, self.patch = YesVersionComponent(), YesVersionComponent(), YesVersionComponent()
        self.prerelease = None
        self.kind = kind_str
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

            if self.major.component is None:
                self.major = YesVersionComponent(part)
                continue

            if self.minor.component is None:
                self.minor = YesVersionComponent(part)
                continue

            if self.patch.component is None:
                self.patch = YesVersionComponent(part)
                continue

            # if we ever get here we've gotten too many components
            raise ValueError('YesVersion received an invalid version string: {}'.format(version_str))

    def get_next_best_versions(self, versions):
        """Given the 'Y' mask, and a set of versions, return a list of all the versions that mask would expect to find
           in the range of versions, but do not actually exists."""
        fake_matches = set()

        if not self.major.is_yes:
            major_versions = [self.major.val()]
        else:
            major_versions = sorted(set([v.major for v in versions]))

        for major in range(min(major_versions), max(major_versions) + 1):
            if not self.minor.is_yes:
                minor_versions = [self.minor.val()]
            else:
                minor_versions = sorted(set([v.minor for v in versions if v.major == major]))

            for minor in range(min(minor_versions), max(minor_versions) + 1):
                if not self.patch.is_yes:
                    patch_versions = [self.patch.val()]
                else:
                    patch_versions = sorted(set([v.patch for v in versions if v.major == major and v.minor == minor]))

                for patch in range(min(patch_versions), max(patch_versions) + 1):
                    fake = _parse_semver("{}.{}.{}".format(major, minor, patch), makefake=True)
                    if fake not in versions:
                        fake_matches.add(fake)

        return fake_matches

    def major_valid(self, version):
        return self.major == version.major

    def minor_valid(self, version):
        return self.minor == version.minor

    def patch_valid(self, version):
        return self.patch == version.patch

    def prerelease_valid(self, version):
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

        return prerelease_valid

    def match(self, version):
        """version matches if all non-YES fields are the same integer number, YES fields match any integer"""
        version = _parse_semver(version)

        return all([self.major_valid(version),
                    self.minor_valid(version),
                    self.patch_valid(version),
                    self.prerelease_valid(version)])

    def __contains__(self, item):
        return self.match(item)

    def __str__(self):
        return ".".join([str(x) for x in [self.major, self.minor, self.patch] if x])


def _parse_semver(version, makefake=False):
    if isinstance(version, semantic_version.Version):
        if makefake:
            version.is_fake = True
        return version
    if isinstance(version, str):
        # strip leading 'v' and '=' chars
        cleaned = version.lstrip('v=')
        try:
            v = semantic_version.Version(cleaned)
        except ValueError:
            v = semantic_version.Version.coerce(cleaned)
            if len(v.build) > 0:
                raise InvalidSemverError('build fields should not be used')
        v.original_string = version
        if makefake:
            v.is_fake = True
        return v
    raise ValueError('version must be either a str or a Version object')
