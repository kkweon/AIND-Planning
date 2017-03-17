#!/bin/bash

function run_test {
    python3 -m unittest $1
}

function run_cargo {
    run_test tests.test_my_air_cargo_problems
}

function run_planning_graph {
    run_test tests.test_my_planning_graph
}

OPTIONS=("Test Air Cargo" "Test Planning Graph" "Test All" "Quit")
PS3="Choice> "
clear
select opt in "${OPTIONS[@]}"
do
    case $opt in
        "Test Air Cargo")
            run_cargo
            break
            ;;
        "Test Planning Graph")
            run_planning_graph
            break
            ;;
        "Test All")
            run_cargo
            run_planning_graph
            break
            ;;
        *)
            echo Quit Selected
            break
            ;;
    esac
done
