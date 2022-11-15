file_contents = open('target.repos').read()

import yaml

yd = yaml.safe_load(file_contents)

#print(yd)

for r, v in yd['repositories'].items():
    # print(r)
    print(' - %s:' % v['type'])
    print('    local-name: %s' % r)
    print('    uri: %s.git' %v['url'])
    print('    version: %s' %v['version'])