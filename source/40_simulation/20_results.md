


## Results



### Screenshots

Two screenshots of the particle simulations are shown below. The first one shows 50000 particle entities colliding in a closed space:

![Particle simulation: screenshot - 50000 colliding particles](source/figures/bench/sc0.png)

The second one shows one of the cells of the spatial partitioning 2D grid - all particles belonging to the cell are highlighted:

![Particle simulation: screenshot - spatial partitioning cell](source/figures/bench/sc1.png)



### Benchmarks {#bench_particlesim}

The computer used to benchmark the particle simulation has the following hardware specifications:

* CPU: [**Intel® Core™ i7-2700K Processor** *(8M Cache, up to 3.90 GHz)*](http://ark.intel.com/products/61275/Intel-Core-i7-2700K-Processor-8M-Cache-up-to-3_90-GHz);

* RAM: [**HyperX Beast 16GB DDR3-2400MHz**](http://www.hyperxgaming.com/us/memory/beast);

* Motherboard: [**ASRock Z77 Extreme4-M**](http://www.asrock.com/mb/intel/z77%20extreme4-m/).

The simulation was executed on a system with [**Arch Linux x64**](https://www.archlinux.org/) as its operating system, using $8$ worker threads. Rendering was disabled for the benchmarks.

`g++` version 6.1.1 was used, with the following compiler flags:\
`-Ofast -march=native -ffast-math -ftree-vectorize`.

The error bars in the following graphs represent the *standard deviation*.

#### Dynamic versus fixed entity storage

![Particle simulation: benchmark results - dynamic entity storage](source/figures/bench/ipcomp_dynamic.png)
![Particle simulation: benchmark results - fixed entity storage](source/figures/bench/ipcomp_fixed.png)

#### Entity scaling

![Particle simulation: benchmark results - 50000 entities](source/figures/bench/entity_50k.png)
![Particle simulation: benchmark results - 100000 entities](source/figures/bench/entity_100k.png)
![Particle simulation: benchmark results - 200000 entities](source/figures/bench/entity_200k.png)



## Conclusions {#bench_parsim_conc}

The following conclusions can be deduced from the benchmark graphs:

* **Fixed** entity storage seems slightly faster than **dynamic** entity storage when inner parallelism is disabled, possibly due to the fact that checks for possible reallocations during entity creations are not present. However, dynamic entity storage seems slightly faster than fixed entity storage when inner parallelism is enabled, even if entity creation only occurs sequentially at the beginning of the simulation. The results on **fixed versus dynamic** entity storage are therefore inconclusive with this benchmark - a different simulation, where entities are continuously created and destroyed over time, may compare the two entity storage strategies more fairly. The tables below shows the execution time percent change of the dynamic storage strategy:

    |      | Fixed (no I.P.) | Dynamic (no I.P.) |
    |------|-----------------|-------------------|
    | 50k  | baseline        | +2.28%            |
    | 100k | baseline        | +1.42%            |
    | 200k | baseline        | +3.56%            |

    |      | Fixed (I.P.) | Dynamic (I.P.) |
    |------|--------------|----------------|
    | 50k  | baseline     | -0.45%         |
    | 100k | baseline     | -0.26%         |
    | 200k | baseline     | -0.44%         |

* As expected, splitting system execution in multiple subtasks using [**inner parallelism**](#multithreading_inner_par) results in a huge run-time performance boost. On the machine used for the benchmarks, an average $65$% relative performance increment is achieved:

    |      | No inner parallelism | Inner parallelism |
    |------|:--------------------:|:-----------------:|
    | 50k  |       baseline       |      -62.32%      |
    | 100k |       baseline       |      -66.38%      |
    | 200k |       baseline       |      -67.07%      |

The complete source code of the example particle simulation can be found in the following GitHub repository, under the *Academic Free License ("AFL") v. 3.0*: [https://github.com/SuperV1234/bcs_thesis](https://github.com/SuperV1234/bcs_thesis).