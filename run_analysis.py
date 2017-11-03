#!/usr/bin/env python

# Copyright 2016 Open Source Robotics Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import os
import subprocess
import yaml



# helpful posts:
# - https://help.github.com/articles/about-git-subtree-merges/
# - https://stackoverflow.com/questions/1683531/how-to-import-existing-git-repository-into-another#


def generate_rosinstall(rosdistro, metapackage='ALL'):
    print("Generating rosinstall for rosdistro: %s metapackage: %s" % (rosdistro, metapackage))
    cmd = ['rosinstall_generator', '--upstream-development', '--deps', '--rosdistro', rosdistro, metapackage]
    return subprocess.check_output(cmd)


def run(cmd, repo_dir):
    print("Running [in directory %s] %s" % (repo_dir, ' '.join(cmd) ))
    subprocess.check_call(cmd, cwd=repo_dir)


def git_check_remote_url(repo_dir, name):
    cmd = ['git', 'config', 'remote.%s.url' % name]
    try:
        return subprocess.check_output(cmd, cwd=repo_dir).rstrip()
    except subprocess.CalledProcessError as ex:
        return None


def import_repo(name, branch, url, repo_dir):
    first_time = not os.path.exists(os.path.join(repo_dir, name))
    if first_time:
        cmd = ['git', 'remote', 'add', name, url]
        run(cmd, repo_dir)
    else:
        # Check for a changed url
        existing_url = git_check_remote_url(repo_dir, name)
        assert existing_url
        if existing_url != url:
            cmd = ['git', 'remote', 'set-url', name, url]
            run(cmd, repo_dir)
    cmd = ['git', 'fetch', name]
    run(cmd, repo_dir)
    cmd = ['git', 'merge', '-s', 'ours', '--no-commit', '%s/%s' % (name, branch)]
    run(cmd, repo_dir)
    # The merge will find the prefix automatically after the first time
    if first_time:
        cmd = ['git', 'read-tree', '--prefix=%s/' % name, '-u', '%s/%s' % (name, branch)]
        run(cmd, repo_dir)
    cmd = ['git', 'commit', '-m', '"Imported %s as a subtree"' % name]
    run(cmd, repo_dir)


def run_gitstats(repository_dir, output_dir):
    gitstats_dir = os.path.join(output_dir, 'gitstats')
    if not os.path.exists(gitstats_dir):
        os.makedirs(gitstats_dir)


    cmd = ['gitstats', repository_dir, gitstats_dir]
    subprocess.check_call(cmd)

def run_cloc(repo_dir, output_dir):
    cmd = ['cloc', repo_dir, '--out=' + os.path.join(output_dir, 'cloc.txt')]
    subprocess.check_call(cmd)


def run_sloccount(repo_dir, output_dir):
    sloccount_file = os.path.join(output_dir, 'sloccount.txt')
    cmd = ['sloccount', repo_dir]
    output = subprocess.check_output(cmd)
    with open(sloccount_file, 'w') as fh:
        fh.write(output)


def setup_aggregate_repo(repo_dir):
    if not os.path.exists(repo_dir):
        print("Setting up aggregate repo %s " % repo_dir)
        os.makedirs(repo_dir)

        cmd = ['git', 'init']
        run(cmd, repo_dir)

        readme = os.path.join(repo_dir, 'README')
        with open(readme, 'w') as fh:
            fh.write("A directory into which to import ROS repos for statistical analysis")
        cmd = ['git', 'add', 'README']
        run(cmd, repo_dir)
        cmd = ['git', 'commit', '-m', '"A repo for ROS statistics"']
        run(cmd, repo_dir)
    else:
        print("Aggregate repo already exists, skipping setup")


def update_aggregate_repsitory(rosinstall_yaml_dict, repo_path):
    errors = {}
    for e in rosinstall_yaml_dict:
        if not 'git' in e:
            print("skipping element %s due to not git" % e)
            continue
        entry = e['git']
        try:
            import_repo(entry['local-name'], entry['version'], entry['uri'], repo_path)
        except subprocess.CalledProcessError as ex:
            errors[entry['local-name']] = str(ex)
    return errors



def main(args):
    errors = {}


    if not args.analyze_only:
        setup_aggregate_repo(args.aggregate_repo_path)
        if args.rosinstall_file:
            with open(args.rosinstall_file, 'r') as fh:
                yaml_file = fh.read()
                print("Using passed rosinstall [%s] instead of generating" % args.rosinstall_file)
        else:
            yaml_file = generate_rosinstall(args.rosdistro, metapackage=args.metapackage)

        yd = yaml.load(yaml_file)

        errors = update_aggregate_repsitory(yd, args.aggregate_repo_path)

    run_gitstats(args.aggregate_repo_path, args.output_dir)
    run_cloc(args.aggregate_repo_path, args.output_dir)
    run_sloccount(args.aggregate_repo_path, args.output_dir)

    print("Errors encountered during cloning include")
    print(errors)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Analyze rosdistros')
    parser.add_argument('--rosdistro', default='indigo',
                        help='The rosdistro to analyze')
    parser.add_argument('--metapackage', default='ALL',
                        help='The metapackage to analyze with all dependencies, or ALL')
    parser.add_argument('--rosinstall-file', action='store',
                        help='Use a rosinstall file passed instead of generating.')
    parser.add_argument('--output-dir', default=None,
                        help='The directory into which to output.')
    parser.add_argument('--aggregate-repo-path', action='store',
                        help=
                        'Generate the aggregate repo into this path, '
                        'default aggregate_<ROSDISTRO>_<METAPACKAGE>.')
    parser.add_argument('--analyze-only', action='store_true',
                        help='Only run the analysis, do not download code.')
    args=parser.parse_args()

    # Check command line for errors
    if args.rosinstall_file:
        if not os.path.exists(args.rosinstall_file):
            parser.error("rosinstall file passed does not exist")
    if args.rosinstall_file and args.metapackage:
        parser.error("Invalid usage, you cannot pass a rosinstall file and a metapackage at the same time.")

    if not args.aggregate_repo_path:
        args.aggregate_repo_path = 'aggregate_%s_%s' % (args.rosdistro, args.metapackage)

    if not args.output_dir:
        args.output_dir = 'output_%s_%s' % (args.rosdistro, args.metapackage)

    main(args)
