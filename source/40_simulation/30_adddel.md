


# Entity creation/destruction benchmark

## Description

The benchmark aims to measure the performance of continuous real-time entity creation/destruction with various combinations of compile-time settings. At the beginning of the application, a fixed number of entities is created. The entities possess a `c::life` component that will destroy them after a random amount of time, creating a new entity instance on destruction. The entity replication process is limited by a counter stored in `c::life` that is decreased on creation.

As with the previous example application, multiple simulations are executed and benchmarked, combining the following compile-time options and parameters:

* Entity count: $50000$, $100000$ and $150000$;

* Inner parallelism: **enabled** or **disabled**;

* Entity storage strategy: **fixed** or **dynamic**.

In total, $12$ simulations are executed.



## Components

The only existing component type is `c::life`.

* **Life**: controls the lifetime of an entity and its amount of replications.

    ```cpp
    struct life
    {
        float _v;
        int _spawns;
    };
    ```


## Systems

* **Life**: deals with entity lifetime and replication. Continuously decreases every particle's `life` value and marks particles as dead when their lifetime is over. Once an entity is marked as dead, a [**deferred function**](#flow_exec_dfuncs) that creates a new particle is enqueued if `c::life::_spawns` is greater than $0$.

    * Multithreading is enabled.


### System implementations

The commented implementation of the `s::life` system is provided below:

```cpp
struct life
{
    template <typename TData>
    void process(ft dt, TData& data)
    {
        data.for_entities([&](auto eid)
            {
                // Alias the entity's lifetime value.
                auto& l = data.get(ct::life, eid)._v;

                // Alias the entity's left replications value.
                auto& spawns = data.get(ct::life, eid)._spawns;

                // Decrease the entity's lifetime.
                l -= 10.f * dt;

                // If the lifetime value reaches zero...
                if(l <= 0.f)
                {
                    // ...mark the entity as dead.
                    data.kill_entity(eid);

                    // If the entity can replicate itself...
                    if(spawns > 0)
                    {
                        // ...enqueue a deferred function creating
                        // a new entity with one less replication.
                        data.defer([spawns](auto& proxy)
                            {
                                mk_particle(proxy, spawns - 1);
                            });
                    }
                }
            });
    }
};
```




## Results



### Benchmarks 

The [previously described machine and environment](#bench_particlesim) were used for this simulation.

Again, the error bars in the following graphs represent the *standard deviation*.

### Dynamic versus fixed entity storage

![Entity add/del: benchmark results - dynamic entity storage](source/figures/bench2/ipcomp_dynamic.png)
![Entity add/del: benchmark results - fixed entity storage](source/figures/bench2/ipcomp_fixed.png)

### Entity scaling

![Entity add/del: benchmark results - 50000 entities](source/figures/bench2/entity_50k.png)
![Entity add/del: benchmark results - 100000 entities](source/figures/bench2/entity_100k.png)
![Entity add/del: benchmark results - 200000 entities](source/figures/bench2/entity_200k.png)



## Conclusions 

<!-- TODO (?) -->

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