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
    mask = 'Y.0.0' # tell me major version changes only once per major version
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.1', '2.0.2']
    current_version = '1.9.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(0 == len(subset))

def test_minor_updates_1():
    mask = 'Y.Y.0' # tell me minor version changes only once per minor version, exclude all patch updates
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.8.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(3 == len(subset))
    assert('1.9.0' in subset)
    assert('1.10.0' in subset)
    assert('2.0.0' in subset)

def test_minor_updates_2():
    mask = 'L.Y.0' # give me minor version changes only for my current major version, exclude all patch updates
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.8.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(3 == len(subset))
    assert('1.9.0' in subset)
    assert('1.10.0' in subset)
    assert('2.0.0' in subset)

def test_all_updates_1():
    mask = 'Y.Y.Y' # Give me every patch, minor and major update
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.8.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(3 == len(subset))
    assert('1.9.0' in subset)
    assert('1.10.0' in subset)
    assert('2.0.0' in subset)


def test_explicit_major_updates_only_1():
    mask = '2.0.0'
    versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', '2.0.0', '2.0.1']
    current_version = '1.9.0'
    subset = VersionFilter.semver_filter(mask, versions, current_version)
    assert(1 == len(subset))
    assert('2.0.0' in subset)
