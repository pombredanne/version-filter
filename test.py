from version_filter import VersionFilter


def test_readme_example_semver():
    mask = 'L.Y.Y'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', 'nightly']
    current_version = '1.9.0'

    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(2 == len(subset))
    assert('1.9.1' in subset)
    assert('1.10.0' in subset)

def test_readme_example_regex():
    mask = 'L.Y.Y'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', 'nightly']
    current_version = '1.9.0'

    subset = VersionFilter.regex_filter(r'^night', versions)
    assert(1 == len(subset))
    assert('nightly' in subset)


def test_major_updates_only_1():
    mask = 'Y.0.0'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.9.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(1 == len(subset))
    assert('2.0.0' in subset)

def test_major_updates_only_2():
    mask = 'Y.0.0'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.1', '2.0.2']
    current_version = '1.9.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(1 == len(subset))
    assert('2.0.1' in subset)

def test_explicit_major_updates_only_1():
    mask = '2.0.0'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.9.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(1 == len(subset))
    assert('2.0.0' in subset)
