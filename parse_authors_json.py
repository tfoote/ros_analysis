#!/usr/bin/env python3

# Collect info from MergeStat json summaries and make into a csv

import json
from pathlib import Path


filename_template = 'mergestat_{year}.json'

unique_authors = {}

for year in range(2008,2023):
    print(f'Year: {year}')
    try:
        with open(filename_template.format(year=year), 'r') as fh:
            json_obj = json.load(fh)
            uauthors = json_obj['uniqueAuthors']
            print(uauthors)
            unique_authors[year] = uauthors
    except:
        print(f'Failed to load year {year}')


with open('unique_authors.csv', 'w') as ofh:
    ofh.write('year, unique_authors\n')
    for y, n in unique_authors.items():
        ofh.write(f'{y}, {n}\n')
