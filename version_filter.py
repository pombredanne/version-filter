from __future__ import unicode_literals
import re
import semantic_version

LOCK = 'L'
YES = 'Y'

class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version):
        """Return a list of versions that are greater than the current version and that match the mask"""
        current = semantic_version.Version(current_version)
        _mask = VersionMask(mask)

        _versions = []
        for version in versions:
            try:
                v = semantic_version.Version(version)
            except ValueError:
                continue  # skip invalid semver strings
            _versions.append(v)
        _versions.sort()

        if _mask.major == LOCK:
            _mask.major = current.major
        if _mask.minor == LOCK:
            _mask.minor = current.minor
        if _mask.patch == LOCK:
            _mask.patch = current.patch

        if 'Y' in mask:
            index = mask.index('Y')
        spec = semantic_version.Spec('{},>{}'.format(mask, current_version))
        selected_versions = [v for v in _versions if v in spec]

        if 'Y' not in mask:
            # if there is no YES in the mask the library should have gotten what we wanted
            return [str(v) for v in selected_versions]

        # if there is at least one YES in the mask, use the rightmost YES to determine the 'precision' of versions to report
        else:
            spec = semantic_version.Spec('>{}'.format(current_version))
            selected_versions = [v for v in _versions if v in spec]
            if _mask.patch == YES:
                pass # they want everything
            if _mask.minor == YES and _mask.patch != YES:
                selected_versions = [x for x in selected_versions if x.patch == 0]
            if _mask.major == YES and _mask.minor != YES and _mask.patch != YES:
                selected_versions = [x for x in selected_versions if x.minor == 0 and x.patch == 0]
            return [str(v) for v in selected_versions]

        # selected_versions = []
        # for v in _versions:
        #     if current >= v:
        #         continue  # skip all versions 'less' than the current version
        #
        #     if mask.major == LOCK and v.major != current.major:
        #         continue  # skip all versions who's major is not locked to the current version
        #
        #     if mask.minor == LOCK and v.minor != current.minor:
        #         continue  # skip all versions who's minor is not locked to the current version
        #
        #     if mask.patch == LOCK and v.patch != current.patch:
        #         continue  # skip all versions who's patch is not locked to the current version
        #
        #     selected_versions.append(v)
        #
        # major_versions = []
        # if mask.major == YES:
        #     major_slots = []
        #     for version in selected_versions:
        #         trunc_version = str(version.major)
        #         if version.major > current.major and trunc_version not in major_slots:
        #             major_slots.append(trunc_version)
        #             major_versions.append(version)
        #
        # minor_versions = []
        # if mask.minor == YES:
        #     minor_slots = []
        #     for version in selected_versions:
        #         trunc_version = '{}.{}'.format(version.major, version.minor)
        #         if version.minor > current.minor and trunc_version not in minor_slots:
        #             minor_slots.append(trunc_version)
        #             minor_versions.append(version)
        #
        # patch_versions = []
        # if mask.patch == YES:
        #     patch_slots = []
        #     for version in selected_versions:
        #         trunc_version = '{}.{}.{}'.format(version.major, version.minor, version.patch)
        #         if version.patch > current.patch and trunc_version not in patch_slots:
        #             patch_slots.append(trunc_version)
        #             patch_versions.append(version)
        #
        # if mask.major == YES or mask.minor == YES or mask.patch == YES:
        #     selected_versions = sorted(list(set(major_versions + minor_versions + patch_versions)))


        return [str(v) for v in selected_versions]

    @staticmethod
    def regex_filter(str, versions):
        """Return a list of versions that match the given regular expression."""
        regex = re.compile(str)
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
            raise ValueError('Invalid SpecItemMask: {}'.format(specitemmask))

        kind, version = match.groups()
        if self.YES in version:
            self.has_yes = True
            v_parts = version.split('.')
            if v_parts[self.MAJOR] == self.YES:
                self.yes_pos = self.MAJOR
            if v_parts[self.MINOR] == self.YES:
                self.yes_pos = self.MINOR
            if v_parts[self.PATCH] == self.YES:
                self.yes_pos = self.PATCH

        if self.LOCK in version:
            self.has_lock = True

        if self.has_lock and not self.current_version:
            raise ValueError('Without a current_version, SpecItemMask objects with LOCKs cannot be converted to Specs')

        if self.has_lock:
            v_parts = version.split('.')
            if v_parts[self.MAJOR] == self.LOCK:
                v_parts[self.MAJOR] = self.current_version.major
            if v_parts[self.MINOR] == self.LOCK:
                v_parts[self.MINOR] = self.current_version.minor
            if v_parts[self.PATCH] == self.LOCK:
                v_parts[self.PATCH] = self.current_version.patch
            version = '.'.join([str(x) for x in v_parts])

        if self.has_yes:
            kind = '*'
            version = ''

        return kind, version


    def get_spec(self):
        return semantic_version.Spec("{}{}".format(self.kind, self.version))


class SpecMask(object):
    def __init__(self, specmask, current_version=None):
        self.speckmask = specmask
        self.current_version = current_version
        self.parse(specmask)
        all_specs = self.specs_ands + self.specs_ors

        # if any of the sp
        if any([s.has_lock for s in all_specs]) and not current_version:
            raise ValueError('SpecMask must be given a current_version if LOCKs are specified')

    def parse(self, specmask):
        self.specs_ors = [x.strip() for x in specmask.split("||")]
        self.specs_ands = [x.strip() for x in specmask.split("&&")]


    def test(self, version):
        pass

    def __str__(self):
        # return self.str
        return '.'.join(str(x) for x in [self.major, self.minor, self.patch] if x != '')