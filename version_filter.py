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
        mask = VersionMask(mask)

        selected_versions = []
        for version in versions:
            try:
                v = semantic_version.Version(version)
            except ValueError:
                continue  # skip invalid semver strings

            if current >= v:
                continue  # skip all versions 'less' than the current version

            if mask.major == LOCK and v.major != current.major:
                continue  # skip all versions who's major is not locked to the current version

            if mask.minor == LOCK and v.minor != current.minor:
                continue  # skip all versions who's minor is not locked to the current version

            if mask.patch == LOCK and v.patch != current.patch:
                continue  # skip all versions who's patch is not locked to the current version

            selected_versions.append(version)

        return selected_versions

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
        return self.str
