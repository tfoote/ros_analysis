#!/bin/bash


AGG_REPO=aggregate_contributors


./run_analysis.py --rosdistro foxy --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro galactic --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro rolling --aggregate-repo-path $AGG_REPO --no-analyze

./run_analysis.py --rosdistro melodic --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro noetic --aggregate-repo-path $AGG_REPO --no-analyze


#./run_analysis.py --rosdistro melodic --aggregate-repo-path $AGG_REPO --analyze-only --output-dir output_contributors

for YEAR in {2008..2022}
do

  docker run -v "${PWD}/$AGG_REPO:/repo" mergestat/mergestat summarize commits --start "$YEAR-01-01" --end "$YEAR-12-31" --json > output_contributors_$YEAR.json

done

python3 parse_authors_json.py
