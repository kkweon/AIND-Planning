#!/bin/bash

function search {
    #timeout in Linux
    gtimeout 5m python3 run_search.py -p $1 -s $2
}

function control_c {
    echo Aborting
    continue
}

if [ -f result.txt ]; then
    echo result.txt exists. It will be deleted.
    rm result.txt
fi

trap control_c SIGINT

# Problem 1, 2, 3
for p in {1..3}
do
    # Search Algorithms 1, ..., 10
    for s in {1..10}
    do
        echo [WIP] Problem: $p Search: $s
        echo Problem: $p Search: $s >> result.txt
        echo ====================== >> result.txt
        search $p $s >> result.txt
    done
done

