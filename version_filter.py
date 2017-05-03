
class VersionFilter(object):

    @staticmethod
    def semver_filter(mask, versions, current_version):
        return versions

    @staticmethod
    def regex_filter(mask, versions, current_versions):
        return versions
