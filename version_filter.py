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


class VersionMask(object):
    def __init__(self, mask_str):
        self.major, self.minor, self.patch = '', '', ''
        self.str = mask_str
        parts = mask_str.split('.')
        if len(parts) >= 3:
            self.patch = parts[2]
        if len(parts) >= 2:
            self.minor = parts[1]
        if len(parts) >= 1:
            self.major = parts[0]
        if len(parts) == 0:
            raise ValueError

    def __str__(self):
        # return self.str
        return '.'.join(str(x) for x in [self.major, self.minor, self.patch] if x != '')