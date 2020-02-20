# Generate Combined Licenses for Swift PM Dependencies

Generate a single `.json` file with the licenses for all Swift Package Manager dependencies of an Xcode Project.

* Python 3
* Swift Package Manager dependencies only
* Tested with Xcode 11.3.1

## Usage Example

As part of an Xcode target's 'Run Script' build phase:

`$SRCROOT/generate-licenses.py --build-dir $BUILD_DIR --output-file $SRCROOT/licenses.json`


## Output Format
```json
{
    "licenses": [
        {
            "libraryName": "",
            "text": ""
        },
        {
            ...
        }
    ]
}
```