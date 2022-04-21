#!/bin/bash


AGG_REPO=all_contributors
OUTPUT_DIR=output_$AGG_REPO

./run_analysis.py --rosdistro foxy --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro galactic --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro rolling --aggregate-repo-path $AGG_REPO --no-analyze

./run_analysis.py --rosdistro melodic --aggregate-repo-path $AGG_REPO --no-analyze
./run_analysis.py --rosdistro noetic --aggregate-repo-path $AGG_REPO --no-analyze


./run_analysis.py --aggregate-repo-path $AGG_REPO --analyze-only --output-dir $OUTPUT_DIR

for YEAR in {2008..2022}
do

  docker run -v "${PWD}/$AGG_REPO:/repo" mergestat/mergestat summarize commits --start "$YEAR-01-01" --end "$YEAR-12-31" --json > $OUTPUT_DIR/mergestat_$YEAR.json

done

(cd $OUTPUT_DIR && python3 ../parse_authors_json.py)
