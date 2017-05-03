# version-filter
A semantic and regex version filtering/masking library

Given a filtering mask or regex and a list of versions (as strings), a subset of that list of versions will be returned.
If a mask is given and the mask uses current version references, an explicit current version must also be provided as an
imput must also be provided as an imput.

## Inputs

### Mask/Regex

### List of version strings

### Current Version

## Usage

```python
from version-filter import VersionFilter

mask = 'L.Y.Y'
versions = ['1.8.0', '1.8.1', '1.8.2', '1.9.0', '1.9.1', '1.10.0', 'nightly']
current_version = '1.9.0'

VersionFilter.semfilter(mask, versions, current_version)
# ['1.9.1', '1.10.0']

VersionFilter.regexfilter(r'^night', versions)
# ['nightly']
```
