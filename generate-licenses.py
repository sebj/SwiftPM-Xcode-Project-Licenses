#!/usr/bin/python
# coding: utf-8

'''
    Generate a single .json file with the licenses for
    all Swift Package Manager dependencies of an Xcode Project.

    :usage: ./licenses.py -b $BUILD_DIR -o licenses.json

    :author: Seb Jachec (https://twitter.com/iamsebj)
'''


from argparse import ArgumentParser, ArgumentTypeError
from glob import glob
import json
import os.path
from sys import argv


__version__ = '0.1'
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
    parser.add_argument('--version', action='version',
                        version='%(prog)s {version}'.format(version=__version__))

    if len(argv) == 1:
        parser.parse_args(['--help'])

    args = parser.parse_args()

    licenses_search_dir = packages_checkouts_dir(args.build_dir_path)
    data = licenses_from_dir(licenses_search_dir)

    with open(args.output_file, 'w') as output_file:
        json.dump(data, output_file, ensure_ascii=False, indent=4)

    return 0

def packages_checkouts_dir(build_directory):
    # Change from <Derived Data>/Build/Products to <Derived Data>/
    derived_data_dir = os.path.dirname(os.path.dirname(build_directory))
    checkouts_dir = os.path.join(derived_data_dir, 'SourcePackages', 'checkouts')
    return checkouts_dir

def licenses_from_dir(directory):
    license_paths = license_paths_from_dir(directory)

    return {
        'licenses': list(map(license_dict_from_file, license_paths))
    }


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


if __name__ == '__main__':
    main(argv)
