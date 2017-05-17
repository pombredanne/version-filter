import re
import semantic_version


class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version):
        """Return a list of versions that are greater than the current version and that match the mask"""
        return versions

    @staticmethod
    def regex_filter(str, versions):
        """Return a list of versions that match the given regular expression."""
        regex = re.compile(str)
        return [v for v in versions if regex.search(v)]
