


# Overview {#part3_sim}

In this part a simple **real-time particle simulation** implemented using ECST will be analyzed, in order to provide the readers with a complete usage example of the library and with performance comparisons between various combinations of the compile-time multithreading options.


## Description

The simulation consists in a number of **rigid-body circular particles** of various radius, colliding with each other in a closed space. The particle entities are generated at the beginning of the demo. A **2D grid** spatial partitioning system is used to speed-up broadphase collision detection. Every particle has a **life** timer that constantly gets decremented: the entity is destroyed as soon as the timer reaches zero. When all the particles are destroyed, the simulation automatically ends.

Multiple simulations are executed and benchmarked, combining the following compile-time options and parameters:

* Entity count: $50000$, $100000$ and $150000$;

* Inner parallelism: **enabled** or **disabled**;

* Entity storage strategy: **fixed** or **dynamic**.

In total, $12$ simulations are executed.

The [SFML](http://sfml-dev.org) library is used for rendering and math utilities.



## Components

Every particle is composed of the following component types:

* **Position**: 2D `float` vector;

    ```cpp
    struct position { sf::Vector2f _v; };
    ```

* **Velocity**: 2D `float` vector;

    ```cpp
    struct velocity { sf::Vector2f _v; };
    ```

* **Acceleration**: 2D `float` vector;

    ```cpp
    struct acceleration { sf::Vector2f _v; };
    ```

* **Color**: used for SFML rendering;

    ```cpp
    struct color { sf::Color _v; };
    ```

* **Circle**: shape of the particle, controls its radius;

    ```cpp
    struct circle { float _radius; };
    ```

* **Life**: controls the lifetime of a particle.

    ```cpp
    struct life { float _v; };
    ```


## Systems

* **Acceleration**: increments each particle's `velocity` vector by its `acceleration` vector;

    * Multithreading is enabled.

* **Velocity**: increments each particle's `position` vector by its `velocity` vector;

    * Multithreading is enabled.

* **Keep in bounds**: keeps every particle inside the boundaries of the simulation;

    * Multithreading is enabled.

* **Spatial partition**: stores the 2D spatial partitioning grid and manages it;

    * Multithreading is enabled;

    * Produces `std::vector<sp_data>` outputs. `sp_data` is a lightweight `struct` holding an `entity_id` and a pair of 2D cells coordinates. The produced vectors will be read from the context step in order to fill the stored 2D grid data structure.

* **Collision detection**: detects collisions between particles *(filtered by the broadphase spartial partitioning system)*. The detected collisions are resolved by a subsequent system;

    * Multithreading is enabled;

    * Produces `std::vector<contact>` outputs. `contact` is a lightweight `struct` holding `entity_id` instances of two colliding particles. The contacts sequentially read from the `solve_contacts` system to solve penetration between particles.

* **Solve contacts**: reads `collision`'s produced `contact` outputs and sequentially solves penetration between particles;

    * Multithreading is disabled.

* **Render colored circle**: deals with particle rendering;

    * Multithreading is enabled;

    * Produces `std::vector<sf::Vertex>` outputs. The vertices are used to render the circles using SFML.

* **Life**: deals with particle lifetime. Continuously decreases every particle's `life` value and marks particles as dead when their lifetime is over;

    * Multithreading is enabled.

* **Fade**: changes particles' opacity depending on their life.

    * Multithreading is enabled.

The implicitly generated depedency DAG is shown below:

\dot(source/figures/generated/sim/dag0 { height=85% })
(Particle simulation: dependency DAG)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=BT

    Acceleration -> Start
    Life -> Start

    Velocity -> Acceleration
    KeepInBounds -> Velocity
    SpatialPartition -> KeepInBounds
    Collision -> SpatialPartition
    SolveContacts -> Collision
    Render -> SolveContacts

    Fade -> Life

    End -> Fade
    End -> Render

    Start [label="", shape="point", width="0.25", height="0.25", fixedsize="true"]

    End [label="", shape="point", width="0.25", height="0.25", fixedsize="true"]
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### System implementations

Most of the system implementations are straightforward: `s::acceleration` and `s::velocity` simply iterate over their subscribed entities, mutating the values of the targeted components. Here is the implementation of `s::acceleration`:

```cpp
struct acceleration
{
    template <typename TData>
    void process(ft dt, TData& data)
    {
        data.for_entities([&](auto eid)
            {
                auto& v = data.get(ct::velocity, eid)._v;
                const auto& a = data.get(ct::acceleration, eid)._v;
                v += a * dt;
            });
    }
};
```

`s::fade`, `s::life` and `s::keep_in_bounds` are implemented in a similar way.



#### Spatial partition

`s::spatial_parititon` is a stateful system: it stores a 2D grid used to speed-up broadphase collisions and produces outputs later read in *step stage* to mutate the stored grid.

The grid is implemented with two nested `std::array` of `std::vector<entity_id>`:

```cpp
struct spatial_partition
{
    using cell_type = std::vector<ecst::entity_id>;
    std::array<std::array<cell_type, grid_height>, grid_width> _grid;
    // ...
```

At the beginning of every step stage `_grid` is cleared. The `process` method of the system iterates over the subscribed entities and produces `sp_data` instances:

```cpp
template <typename TData>
void process(TData& data)
{
    // Get a reference to the output vector and clear it.
    auto& o = data.output();
    o.clear();

    // For every entity in the subtask...
    data.for_entities([&](auto eid)
        {
            // Access component data.
            const auto& p = data.get(ct::position, eid)._v;
            const auto& c = data.get(ct::circle, eid)._radius;

            // Figure out the broadphase cell and emplace an
            // `sp_data` instance in the output vector.
            this->for_cells_of(p, c, [eid, &o](auto cx, auto cy)
                {
                    o.emplace_back(eid, cx, cy);
                });
        });
}
```

The `sp_data` struct is defined as follows:

```cpp
struct sp_data
{
    ecst::entity_id _e;
    sz_t _cell_x, _cell_y;
};
```

Every subtask of `s::spatial_partition` will produce `sp_data` instances in parallel. They will be sequentially read in the step stage to fill the 2D grid:

```cpp
sea::t(st::spatial_partition).detailed_instance(
    [&proxy](auto& instance, auto& executor)
    {
        // Clear 2D grid.
        auto& s(instance.system());
        s.clear_cells();

        // Produce `sp_data` instances in parallel.
        executor.for_subtasks([&s](auto& data)
            {
                s.process(data);
            });

        // Fill 2D grid sequentially.
        instance.for_outputs(
            [](auto& xs, auto& sp_vector)
            {
                for(const auto& x : sp_vector)
                {
                    xs.add_sp(x);
                }
            });
    }));
```



#### Collision

The `s::collision` system will iterate over unique pairs of particles in the same spatial partitioning cell and produce `contact` instances in parallel that will be sequentially processed by the `s::solve_contacts` system.

The `contact` struct is defined as follows:

```cpp
struct contact
{
    // IDs of the colliding entities.
    ecst::entity_id _e0, _e1;

    // Distance between entities.
    float _dist;
};
```

As `s::spatial_parititon` is a dependency of `s::collision`, its state can be safely accessed in `s::collision::process`:

```cpp
template <typename TData>
void process(TData& data)
{
    // Get a reference to the output vector and clear it.
    auto& out = data.output();
    out.clear();

    // Get a reference to the `spatial_partition` system.
    auto& sp = data.system(st::spatial_partition);

    // For every entity in the subtask...
    data.for_entities([&](auto eid)
        {
            // Access the grid cell containing position `p0`.
            auto& p0 = data.get(ct::position, eid)._v;
            auto& cell = sp.cell_by_pos(p0);

            for_unique_pairs(cell, eid, [&](auto eid2)
                {
                    // Check "circle vs circle" collision
                    // and eventually emplace a `contact`
                    // instance in `out`.
                });
        });
}
```