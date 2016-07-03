#!/bin/bash

mkdir -p "./temp"
mkdir -p "./output"
mkdir -p "./source/figures/generated/ecs/overview/oop"
mkdir -p "./source/figures/generated/ecs/overview/oop_composition"
mkdir -p "./source/figures/generated/ecs/overview/dod_composition"
mkdir -p "./source/figures/generated/ecst/overview/multithreading/outer"
mkdir -p "./source/figures/generated/ecst/overview/multithreading/inner"
mkdir -p "./source/figures/generated/ecst/architecture"
mkdir -p "./source/figures/generated/ecst/compiletime"
mkdir -p "./source/figures/generated/ecst/flow"
mkdir -p "./source/figures/generated/sim"

# make pdf && (chromium ./output/thesis.pdf &)&
make pdf && (evince ./output/thesis.pdf &)&