#!/usr/bin/python
# coding: utf-8

'''
    Generate a single .json file with the licenses for
    all Swift Package Manager dependencies of an Xcode Project.

    :usage: ./licenses.py -b $BUILD_DIR -p $PROJECT_DIR/ProjectName.xcodeproj -o $SRCROOT/licenses.json

    :author: Seb Jachec (https://twitter.com/iamsebj)
'''


from argparse import ArgumentParser, ArgumentTypeError
from glob import glob
import json
import os.path
from sys import argv
import urlparse


__version__ = '0.2'
DESCRIPTION = '''Generate a single .json file with the licenses for
 all Swift Package Manager dependencies of an Xcode Project.'''

def build_dir_type(string):
    if not os.path.isdir(string):
        raise ArgumentTypeError('Invalid build directory path: % s' % string)
    return string


def output_file_type(string):
    if '.json' not in string:
        raise ArgumentTypeError(
            'Output file path must contain .json extension')
    return string

def xcode_proj_type(string):
    if not os.path.isdir(string):
        raise ArgumentTypeError('Invalid project path: % s' % string)
    if '.xcodeproj' not in string:
        raise ArgumentTypeError(
            'Invalid --project_file argument: % s' % string)
    return string

def xcode_workspace_type(string):
    if not os.path.isdir(string):
        raise ArgumentTypeError('Invalid project path: % s' % string)
    if '.xcworkspace' not in string:
        raise ArgumentTypeError(
            'Invalid --workspace_file argument: % s' % string)
    return string


def main(_):
    parser = ArgumentParser(description=DESCRIPTION)
    parser.add_argument('-b', '--build-dir',
                        dest='build_dir_path',
                        metavar='build_dir',
                        help='build directory, usually BUILD_DIR',
                        type=build_dir_type)
    parser.add_argument('-o', '--output-file',
                        dest='output_file',
                        metavar='output_file',
                        help='path to the .json licenses file to be generated',
                        type=output_file_type)
    parser.add_argument('-p', '--project-file',
                        dest='project_file',
                        metavar='project_file',
                        help='path to the .xcodeproj',
                        type=xcode_proj_type)
    parser.add_argument('-w', '--workspace-file',
                        dest='workspace_file',
                        metavar='workspace_file',
                        help='path to the .xcworkspace',
                        type=xcode_workspace_type)
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))

    if len(argv) == 1:
        parser.parse_args(['--help'])

    args = parser.parse_args()

    # Read all licenses from derived data folder where SPM has checked out the source for each one
    licenses_search_dir = packages_checkouts_dir(args.build_dir_path)
    licenses_info = licenses_from_dir(licenses_search_dir)

    if args.project_file:
        # Read Package.resolved file for the project to get name, url and version information for each dependency
        package_path = resolved_package_path_from_proj(args.project_file)
    elif args.workspace_file:
        # Read Package.resolved file for the workspace to get name, url and version information for each dependency
        package_path = resolved_package_path_from_workspace(args.workspace_file)
    else:
        # No project/workspace specified so return licenses from derived data
        # This ensures backwards compatability 
        write_to_output(licenses_info, args.output_file)
        return 0

    packages = list(map(dependency_from_resolved_package, load_resolved_packages(package_path)))

    # Combine the licenses with the package information
    update_packages_with_licenses(packages, licenses_info)

    write_to_output(packages, args.output_file)

    return 0

def packages_checkouts_dir(build_directory):
    # Change from <Derived Data>/Build/Products to <Derived Data>/
    derived_data_dir = os.path.dirname(os.path.dirname(build_directory))
    checkouts_dir = os.path.join(derived_data_dir, 'SourcePackages', 'checkouts')
    return checkouts_dir

def resolved_package_path_from_proj(proj_directory):
    # Check *.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved
    package_path = os.path.join(proj_directory, 'project.xcworkspace', 'xcshareddata', 'swiftpm', 'Package.resolved')
    return package_path

def resolved_package_path_from_workspace(workspace_directory):
    # Check *.xcworkspace/xcshareddata/swiftpm/Package.resolved
    package_path = os.path.join(workspace_directory, 'xcshareddata', 'swiftpm', 'Package.resolved')
    return package_path

def licenses_from_dir(directory):
    license_paths = license_paths_from_dir(directory)

    return list(map(license_dict_from_file, license_paths))


def is_license_file(path):
    name = os.path.basename(path).lower()
    return name.startswith('license') or name.startswith('licence')


def license_paths_from_dir(directory):
    file_paths = glob(os.path.join(directory, '*/*'))
    return filter(is_license_file, file_paths)


def license_dict_from_file(path):
    parent_directory = os.path.dirname(path)
    parent_directory_name = os.path.basename(parent_directory)

    with open(path, 'r') as file:
        text = file.read().rstrip()

    return {
        'libraryName': parent_directory_name,
        'text': text
    }

def load_resolved_packages(path):
    with open(path, 'r') as file:
        text = file.read()

    packages_data = json.loads(text)
    return packages_data['object']['pins']

def dependency_from_resolved_package(package):
    return {
        'name': package['package'],
        'version': package['state']['version'],
        'url': package['repositoryURL']
        }

def extract_repo_name_from_url(url):
    url_components = urlparse.urlparse(url)
    path = url_components.path
    repo_name = path.rpartition('/')[-1].replace('.git', '')
    return repo_name

def update_packages_with_licenses(packages, licenses_info):
    for package in packages:
        url = package['url']
        repo_name = extract_repo_name_from_url(url)
        matchingLicenseInfo = filter(lambda x: x['libraryName'] == repo_name, licenses_info)
        if matchingLicenseInfo:
            package['text'] = matchingLicenseInfo[0]['text']
            # Keeping libraryName for backwards compatability
            package['libraryName'] = matchingLicenseInfo[0]['libraryName']

def write_to_output(licenses_list, output_file):
    with open(output_file, 'w') as output_file:
        json.dump({'licenses': licenses_list}, output_file, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    main(argv)
