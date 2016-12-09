#!/usr/bin/env python

import os
import subprocess
import yaml

agg_dir = 'aggrepo'
output_dir = 'output'
input_file = 'all.rosinstall'

errors = {}

# helpful posts:
# - https://help.github.com/articles/about-git-subtree-merges/
# - https://stackoverflow.com/questions/1683531/how-to-import-existing-git-repository-into-another#

def run(cmd, agg_dir):
    print("Running [in directory %s] %s" % (agg_dir, ' '.join(cmd) ))
    subprocess.check_call(cmd, cwd=agg_dir)

def import_repo(name, branch, url, agg_dir):
    cmd = ['git', 'remote', 'add', name, url]
    run(cmd, agg_dir)
    cmd = ['git', 'fetch', name]
    run(cmd, agg_dir)
    cmd = ['git', 'merge', '-s', 'ours', '--no-commit', '%s/%s' % (name, branch)]
    run(cmd, agg_dir)
    cmd = ['git', 'read-tree', '--prefix=%s/' % name, '-u', '%s/%s' % (name, branch)]
    run(cmd, agg_dir)
    cmd = ['git', 'commit', '-m', '"Imported %s as a subtree"' % name]
    run(cmd, agg_dir)


if not os.path.exists(agg_dir):
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

with open(input_file, 'r') as fh:
    yaml_file = fh.read()

yd = yaml.load(yaml_file)

for e in yd:
    if not 'git' in e:
        print("skipping element %s due to not git" % e)
        continue
    entry = e['git']
    if os.path.exists(os.path.join(agg_dir, entry['local-name'])):
        print("skipping element which already has a directory %s" % entry['local-name'])
        continue
    try:
        import_repo(entry['local-name'], entry['version'], entry['uri'], agg_dir)
    except subprocess.CalledProcessError as ex:
        errors[entry['local-name']] = str(ex)

gitstats_dir = os.path.join(output_dir, 'gitstats')
if not os.path.exists(gitstats_dir):
    os.makedirs(gitstats_dir)


cmd = ['gitstats', agg_dir, gitstats_dir]
subprocess.check_call(cmd)


cmd = ['cloc', agg_dir, '--out=' + os.path.join(output_dir, 'cloc.txt')]
subprocess.check_call(cmd)

sloccount_file = os.path.join(output_dir, 'sloccount.txt')
cmd = ['sloccount', agg_dir]
output = subprocess.check_output(cmd)
with open(sloccount_file, 'w') as fh:
    fh.write(output)


print("Errors encountered include")
print(errors)
