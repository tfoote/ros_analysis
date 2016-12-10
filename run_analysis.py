#!/usr/bin/env python

import os
import subprocess
import yaml




agg_dir = 'aggrepo'
output_dir = 'output'

rosdistro = 'indigo'
metapackage = 'ALL'

#input_file = 'all.rosinstall'




# helpful posts:
# - https://help.github.com/articles/about-git-subtree-merges/
# - https://stackoverflow.com/questions/1683531/how-to-import-existing-git-repository-into-another#


def generate_rosinstall(rosdistro, metapackage='ALL'):
    print("Generating rosinstall for rosdistro: %s metapackage: %s" % (rosdistro, metapackage))
    cmd = ['rosinstall_generator', '--upstream-development', '--deps', '--rosdistro', rosdistro, metapackage]
    return subprocess.check_output(cmd)


def run(cmd, agg_dir):
    print("Running [in directory %s] %s" % (agg_dir, ' '.join(cmd) ))
    subprocess.check_call(cmd, cwd=agg_dir)


def git_check_remote_url(repo_dir, name):
    cmd = ['git', 'config', 'remote.%s.url' % name]
    try:
        return subprocess.check_output(cmd, cwd=agg_dir).rstrip()
    except subprocess.CalledProcessError as ex:
        return None


def import_repo(name, branch, url, agg_dir):
    first_time = not os.path.exists(os.path.join(agg_dir, name))
    if first_time:
        cmd = ['git', 'remote', 'add', name, url]
        run(cmd, agg_dir)
    else:
        # Check for a changed url
        existing_url = git_check_remote_url(agg_dir, name)
        assert existing_url
        if existing_url != url:
            cmd = ['git', 'remote', 'set-url', name, url]
            run(cmd, agg_dir)
    cmd = ['git', 'fetch', name]
    run(cmd, agg_dir)
    cmd = ['git', 'merge', '-s', 'ours', '--no-commit', '%s/%s' % (name, branch)]
    run(cmd, agg_dir)
    # The merge will find the prefix automatically after the first time
    if first_time:
        cmd = ['git', 'read-tree', '--prefix=%s/' % name, '-u', '%s/%s' % (name, branch)]
        run(cmd, agg_dir)
    cmd = ['git', 'commit', '-m', '"Imported %s as a subtree"' % name]
    run(cmd, agg_dir)


def run_gitstats(repository_dir, output_dir):
    gitstats_dir = os.path.join(output_dir, 'gitstats')
    if not os.path.exists(gitstats_dir):
        os.makedirs(gitstats_dir)


    cmd = ['gitstats', repository_dir, gitstats_dir]
    subprocess.check_call(cmd)

def run_cloc(agg_dir, output_dir):
    cmd = ['cloc', agg_dir, '--out=' + os.path.join(output_dir, 'cloc.txt')]
    subprocess.check_call(cmd)


def run_sloccount(agg_dir, output_dir):
    sloccount_file = os.path.join(output_dir, 'sloccount.txt')
    cmd = ['sloccount', agg_dir]
    output = subprocess.check_output(cmd)
    with open(sloccount_file, 'w') as fh:
        fh.write(output)


def setup_aggregate_repo(agg_dir):
    if not os.path.exists(agg_dir):
        print("Setting up aggregate repo %s " % agg_dir)
        os.makedirs(agg_dir)

        cmd = ['git', 'init']
        run(cmd, agg_dir)

        readme = os.path.join(agg_dir, 'README')
        with open(readme, 'w') as fh:
            fh.write("A directory into which to import ROS repos for statistical analysis")
        cmd = ['git', 'add', 'README']
        run(cmd, agg_dir)
        cmd = ['git', 'commit', '-m', '"A repo for ROS statistics"']
        run(cmd, agg_dir)
    else:
        print("Aggregate repo already exists, skipping setup")


def main():
    setup_aggregate_repo(agg_dir)

    # TODO arg parsing for custom rosinstall file
    #with open(input_file, 'r') as fh:
    #    yaml_file = fh.read()

    yaml_file = generate_rosinstall(rosdistro)

    yd = yaml.load(yaml_file)

    errors = {}
    for e in yd:
        if not 'git' in e:
            print("skipping element %s due to not git" % e)
            continue
        entry = e['git']
        try:
            import_repo(entry['local-name'], entry['version'], entry['uri'], agg_dir)
        except subprocess.CalledProcessError as ex:
            errors[entry['local-name']] = str(ex)


    run_gitstats(agg_dir, output_dir)
    run_cloc(agg_dir, output_dir)
    run_sloccount(agg_dir, output_dir)

    print("Errors encountered during cloning include")
    print(errors)


if __name__ == "__main__":
    main()
