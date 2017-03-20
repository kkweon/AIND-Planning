#!/bin/bash

if [ -d "submit" ]; then 
    rm -rf "submit"
fi
mkdir submit 
cp my_air_cargo_problems.py submit/
cp my_planning_graph.py submit/
cp reports/heuristic_analysis.pdf submit/
cp reports/research_review.pdf submit/
