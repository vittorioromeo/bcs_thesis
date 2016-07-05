


# Overview {#part2_ecst}

**ECST** is a **C++14** library designed to let users implement the **Entity-Component-System** pattern in their applications leveraging **compile-time** knowledge of component types, data-structures and system dependencies to allow **automatic parallelization** of separate data transformation chains.

The source code is available on GitHub under the *Academic Free License ("AFL") v. 3.0*: [https://github.com/SuperV1234/ecst](https://github.com/SuperV1234/ecst).

## Design

The library was designed to allow users to safely implement the ECS pattern using an **high-level of abstraction** without sacrificing **performance** and **flexibility**, using knowledge of the supported component and system types at compile-time.

### Compile-time ECS

Every feature offered by ECST requires the instantiation of a **context** template class *(whose role is the management of the entire pattern)* which provides the user with a high-level interface to interact with entities, components and systems. The context object requires **prior knowledge** of all **component types** and **system types** at compile-time. Additionally, options regarding multithreading support, system scheduling and entity limits can be specified before the instantiation of a context.

Due to these factors, ECST is **not a data-driven** Entity-Component-System library. If the target application domain requires dynamic run-time composition and flexibility, it is sensible *(and recommended)* to use ECST with an additional data-driven ECS library[^runtime_features].

* All component and system types must be known at compile-time.

* Entities can be created, destroyed, tracked and mutated at run-time.

Some disadvantages of this approach include:

* Longer and potentially-unreadable errors.

* Increased compilation times.

The implementation details regarding the definition and usage of compile-time settings will be explored in [Chapter 6](#chap_ecst_metaprogramming) and [Chapter 7](#chap_ecst_compilemtime). To make the following points simpler to understand and to give the readers an idea of the previously mentioned limitations and features, the code snippet below will illustrate how context objects are configured and instantiated in the user code.

#### Code example: settings definition {#code_example_settings_definition}

Imagine a 2D particle simulation composed by:

* Three component types: **Position**, **Velocity**, and **Acceleration**.

* Two system types: **Velocity** and **Acceleration**.

Component types are defined as simple **POD** *(plain-old-data)* `struct` types.

```cpp
// The namespace `c` will contain all component types.
namespace c
{
    struct position { /* ... */ };
    struct velocity { /* ... */ };
    struct acceleration { /* ... */ };
}
```

System types are declared as `struct` types that will eventually be defined alongside their processing logic.

```cpp
//The namespace `s` will contain all system types.
namespace s
{
    struct velocity;
    struct acceleration;
}
```

ECST makes heavy use of the **type-value-encoding** *(a.k.a. dependent typing)* meta-programming paradigm. It is necessary to define wrapper `constexpr` **tag** values that will store the type information of components and systems: tags are be used to greatly simplify both the user interface *(as accessing template methods in C++ requires the cumbersome `.template` disambiguation syntax)* and implementation code.

Component tags are defined using `ecst::tag::component::v`:

```cpp
// The namespace `ct` will contain all component tags.
namespace ct
{
    constexpr auto position =
        ecst::tag::component::v<c::position>;

    constexpr auto velocity =
        ecst::tag::component::v<c::velocity>;

    constexpr auto acceleration =
        ecst::tag::component::v<c::acceleration>;
}
```

System tags are defined using `ecst::tag::system::v`:

```cpp
// The namespace `st` will contain all system tags.
namespace st
{
    constexpr auto velocity =
        ecst::tag::system::v<c::velocity>;

    constexpr auto acceleration =
        ecst::tag::system::v<c::acceleration>;
}
```

The verbosity of the code shown above can be avoided through the use of convenient preprocessor macros. The definition of tag objects only needs to occur once in the entire user codebase.

Having defined all required types and tags, the next step will consist in defining *signatures*:

* **Component signatures** bind component tags to **storage policies**.

* **System signatures** bind system tags to multiple settings which will be analyzed in depth in [Chapter 7](#system_sigs): **parallelization policies** and **dependencies** can be found among them.

Signatures are stored in compile-time type lists called **signature lists**, which must be forwarded to the context creation, in order to instantiate a context object.

The `make_csl()` function will create a component signature for every previously-defined component tag, and will return a component signature list holding all of them.

```cpp
constexpr auto make_csl()
{
    // Component signature namespace aliases.
    namespace sc = ecst::signature::component;
    namespace slc = ecst::signature_list::component;

    // Store `c::acceleration`, `c::velocity` and `c::position` in
    // three separate contiguous buffers (SoA).
    constexpr auto cs_acceleration =
        sc::make(ct::acceleration).contiguous_buffer();

    constexpr auto cs_velocity =
        sc::make(ct::velocity).contiguous_buffer();

    constexpr auto cs_position =
        sc::make(ct::position).contiguous_buffer();

    // Build and return the "component signature list".
    return slc::make(cs_acceleration, cs_velocity, cs_position);
}
```

The `make_ssl()` function will create a system signature for every previously-defined system tag, and will return a system signature list holding all of them.

```cpp
constexpr auto make_ssl()
{
    // System signature namespace aliases.
    namespace ss = ecst::signature::system;
    namespace sls = ecst::signature_list::system;

    // Acceleration system signature.
    constexpr auto ss_acceleration =
        ss::make(st::acceleration)
            .parallelism(split_evenly_per_core)
            .read(ct::acceleration)
            .write(ct::velocity);

    // Velocity system signature.
    constexpr auto ss_velocity =
        ss::make(st::velocity)
            .dependencies(st::acceleration)
            .parallelism(split_evenly_per_core)
            .read(ct::velocity)
            .write(ct::position);

    // Build and return the "system signature list".
    return sls::make(ss_acceleration, ss_velocity);
}
```

The final setup step consists in the definition of a `constexpr` **context settings** instance, which will be used to instantiate an ECST context.

```cpp
constexpr auto context_settings =
    ecst::settings::make()
        .component_signatures(make_csl())
        .system_signatures(make_ssl())

auto context =
    ecst::context::make(context_settings);
```

Note that this example skipped many possible configuration options and implementation and design details for the current settings definition approach: the goal of the code snippets above is to clarify that component and system types *need* to be known at compile-time and *how* that information is passed to an ECST context. The knowledge provided by `context_settings` will be used to **generate** the following elements at **compile-time**:

* Storage for [**entity metadata**](#storage_entity), [**component data**](#storage_component), and [**systems**](#storage_system).

* An implicit **system dependency graph**, which is used to automatically run different systems in parallel.

Easily interchangeable compile-time options also allow developers to experiment with different data layouts and scheduling policies without having to modify the application code.



### Customizability

The compile-time-driven nature of the library lends itself to **policy-based design** for user-configurable options. In line with the *"pay for what you use"* C++ philosophy, the specified policies are taken into account in various ways to optimize run-time performance and memory usage.

All featured options will be analyzed in [Chapter 7](#chap_ecst_compiletime). As a simple example, the following code snippet that generates two different context instances can help understand the power of policy-based settings:

#### Code example: policy-based customization

```cpp
constexpr auto context_settings_0 =
    ecst::settings::make()
        .allow_inner_parallelism()
        .fixed_entity_limit(ecst::sz_v<10000>);

constexpr auto context_settings_1 =
    ecst::settings::make()
        .disallow_inner_parallelism()
        .dynamic_entity_limit()
        .scheduler(cs::scheduler<user_defined_scheduler>);
```

Note how easy and intuitive it is to change major library components and affect the flexibility and performance of user applications. This pattern is not only used in context settings definition, but also in component and system signatures *(e.g. inner parallelism policies or system dependencies)*.

The approach also favours **test-driven-development** and application code **transparency**: tests and benchmarks covering various combinations of policies *(either exhaustively or with a fuzzy approach)* can be easily generated by using nested compile-time loops over desired policy lists, thus providing information regarding the correctness and performance of the user code.



### Abstraction, user-friendliness, and safety

A common misconception regarding **data-oriented design** is that it's necessary to sacrifice **encapsulation** and to **reduce the level of abstraction** in order to achieve performance and cache-friendliness. The following beliefs are commonly found in online discussions:

* High-level multi-paradigm languages like **C++14** or **D** are not suitable for high-performance DOD because they inherently drive programmers to design highly-abstracted code that is not closely mapped to the machine hardware. The origin of this belief can be attributed to the abuse of OOP techniques, such as run-time polymorphism and encapsulation, which tend to increase the level of abstraction, with the side-effect of harming data locality and leading to suboptimal memory layouts.

* Every abstraction has an intrinsic cost *("there is no such thing as cost-free abstractions")*.

These misbeliefs may result in the fallacy that performant DOD code must be devoid of high-level abstractions.

ECST aims to *counter this fallacy* by providing a high-level interface that does not sacrifice run-time performance thanks to C++14 **cost-free abstractions**. Benefits of a highly-abstracted data-oriented ECS library include:

* **User-friendly** and **transparent** syntax. No explicit storage or pointer management is required, and application code is independent of user-defined settings and policies.

* Higher **safety**, as many development mistakes regarding dependencies and data access can be caught at compile-time.

* Easier **testability**, due to the fact that abstracting settings and policies allows tests to run comprehensively over a wide set of option combinations.

    * Closely related, the possibility of quickly **experimenting** with different strategies is also a major benefit of a higher abstraction level.

* **Encapsulation**, **reusability**, and fulfillment of the **DRY** principle: abstracting and templatizing storage strategies and policies allows code to be conveniently reused.

#### Syntax-level transparency {#ecstoverview_syntaxtransp}

One important design goal of ECST is allowing the user to experiment with different policies, schedulers and execution methods **without having to explicitly change the application code**. This objective is achieved through the use of **proxy** objects and heavily-templatized type-value-encoding implementation code. The result is a **syntax-level transparency** that allows the application code to be completely independent of compile-time policies/strategies.

Proxies and transparency implementation details will be covered in [Chapter 11](#chap_proxies) - a simple code example will illustrate one possible use of syntax-level transparency through proxies.

#### Code example: transparency through proxies

Here's a possible implementation of the `s::velocity` system declared in [the previous settings definition subsection](#code_example_settings_definition):

```cpp
struct velocity
{
    template<typename TData>
    void process(TData& data)
    {
        data.for_entities([](auto eid)
        {
            auto& position =
                data.get(ct::position, eid)._v;

            const auto& velocity =
                data.get(ct::velocity, eid)._v;

            position += velocity;
        });
    }
};
```

The `velocity` system `struct` contains a `process` template method that takes a single `TData& data` *lvalue reference* as its argument *(note that `process` is not a special method that is specifically recognized by ECST)*. `data` is a **data proxy** object, which abstracts the operations of a system behind a **safe and transparent** interface.

By invoking the `data.for_entities` method with a callable object, it is possible to iterate over the entities subscribed to the system, and perform some actions on the component they own. In this case, we're accessing the `c::position` component through a mutable reference, and the `c::velocity` component through a `const` reference, in order to move the particle by its velocity.

The interesting thing is that this syntax is **completely independent** of the system settings and execution policies - the system's dependencies or parallelism policies do not matter to the data proxy. Other things to take notice of are:

* The storage policy of the components is irrelevant. `c::position` and `c::velocity` could be stored in the same contiguous buffer, or one of them could be in an hash-map while the other one is in a machine on the other side of the world *(storing a component in a different continent could slightly affect the performance of your application)*.

* Getting a mutable or `const` reference to a component is **statically checked** at compile-time, producing an error in case the component access does not fulfill what was specified in the system signature.

* `process` is not special, and not limited to a single argument - additional data could be passed to the method and captured in the lambda. This will be covered in detail in [Chapter 8](#chap_flow) - here's a possible way of invoking `s::velocity::process`:

    ```cpp
    namespace sea = ecst::system_execution_adapter;

    context.step([](auto& proxy)
    {
        proxy.execute_systems(
            sea::t(st::velocity).for_subtasks(
                [](auto& s, auto& data)
                {
                    s.process(data);
                })
        );
    });
    ```

### Multithreading model

The library was designed with user-friendly multithreading as one of the primary goals, which is achieved by providing two levels of parallelism that considerably increase application performance in the presence of multiple CPU cores: **"outer parallelism"** and **"inner parallelism"**.

Multithreading support is enabled by default, but can be switched off completely or only in particular systems.

#### Outer parallelism {#overview_outer_parallelism_dag}

**"Outer parallelism"** is the term used in ECST which defines the concept of running multiple systems that do not depend on each other in parallel. Its implementation details will be analyzed in [Chapter 10](#multithreading_system_scheduling). Conceptually, an **implicit directed acyclic graph** is created at compile-time thanks to the knowledge of system dependencies. The execution of the implicit DAG is handled by a **system scheduler** type specified during settings definition.

Consider the previously defined system signatures - an implicit DAG isomorphic to the one below will be generated by ECST *(arrows between nodes should be read as "depends on")*:

\dot(source/figures/generated/ecst/overview/multithreading/outer/dag0 { width=50% })
(ECST multithreading: example outer parallelism DAG #0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=RL
    Velocity -> Acceleration
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The graph makes it obvious that no outer parallelism can take place here. Increasing the number of component and system types introduces separate dependency chains - imagine the addition of **Growth**, **Shape**, **Rotation** and **Rendering** systems for a graphical particle simulation:

\dot(source/figures/generated/ecst/overview/multithreading/outer/dag1 { width=65% })
(ECST multithreading: example outer parallelism DAG #1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=RL
    Velocity -> Acceleration
    Growth -> Shape
    Rendering -> Growth
    Rendering -> Velocity
    Rendering -> Rotation
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The DAG now shows three separate dependency chains:

* Rendering → Velocity → Acceleration.

* Rendering → Growth → Shape.

* Rendering → Rotation.

The chains starting with **Acceleration**, **Shape** and **Rotation** can be executed in parallel. The **Rendering** system will wait until all three chains have been successfully executed, then it will process its subscribed entities.

Note that the user does not have to specify these chains anywhere - they are implicitly created thanks to the dependencies described during system signature definition.



#### Inner parallelism

Other that running separate systems in parallel, ECST supports splitting a single system into multiple **sub-tasks**, which can be executed on separate threads. Many systems, such as the ones that represent functionally pure computations, do not contain *side-effects* that modify their own state or that define interactions between the subscribed entities: these are prime examples of **"embarrassingly parallel"** computations. In contrast, some systems *(e.g. broad-phase collision spatial partitioning)* require processing their subscribed entities on a single thread, in order to update data structures without explicit locking mechanisms[^explicit_locking_mechanisms].

The aforementioned **Velocity** and **Acceleration** systems are suited for inner parallelism. The user can enable inner parallelism when defining system signatures, also choosing an **inner parallelism strategy** that can be generated by composing multiple strategies together *(e.g. "split into 4 sub-tasks only if subscribed entity count is more than 100000")*.

Imagine applying a *"split into 4 sub-tasks"* strategy to **Velocity** and **Acceleration** - the resulting DAG would look as follows:

\dot(source/figures/generated/ecst/overview/multithreading/inner/dag0)
(ECST multithreading: example inner parallelism DAG)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=RL

    Velocity_Fork [shape=rectangle, label="Velocity (fork)"];
    Velocity_Join [shape=rectangle, label="Velocity (join)"];
    Acceleration_Fork [shape=rectangle, label="Acceleration (fork)"];
    Acceleration_Join [shape=rectangle, label="Acceleration (join)"];

    Velocity_0 [shape="circle", label="0", width=".2", height=".2", fixedsize="true"];
    Velocity_1 [shape="circle", label="1", width=".2", height=".2", fixedsize="true"];
    Velocity_2 [shape="circle", label="2", width=".2", height=".2", fixedsize="true"];
    Velocity_3 [shape="circle", label="3", width=".2", height=".2", fixedsize="true"];

    Acceleration_0 [shape="circle", label="0", width=".2", height=".2", fixedsize="true"];
    Acceleration_1 [shape="circle", label="1", width=".2", height=".2", fixedsize="true"];
    Acceleration_2 [shape="circle", label="2", width=".2", height=".2", fixedsize="true"];
    Acceleration_3 [shape="circle", label="3", width=".2", height=".2", fixedsize="true"];

    subgraph velocity
    {
        Velocity_0 -> Velocity_Fork
        Velocity_1 -> Velocity_Fork
        Velocity_2 -> Velocity_Fork
        Velocity_3 -> Velocity_Fork
        Velocity_Join -> Velocity_0
        Velocity_Join -> Velocity_1
        Velocity_Join -> Velocity_2
        Velocity_Join -> Velocity_3
    }

    subgraph acceleration
    {
        Acceleration_Join -> Acceleration_0
        Acceleration_Join -> Acceleration_1
        Acceleration_Join -> Acceleration_2
        Acceleration_Join -> Acceleration_3
        Acceleration_0 -> Acceleration_Fork
        Acceleration_1 -> Acceleration_Fork
        Acceleration_2 -> Acceleration_Fork
        Acceleration_3 -> Acceleration_Fork
    }

    Velocity_Fork -> Acceleration_Join
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This allows the $0..4$ sub-tasks to run in parallel. Commonly, **inner parallelism executors**, which implement inner parallelism policies, simply split the subscribed entities of a system evenly between the generated subtasks. The *"fork"* and *"join"* nodes present in the DAG are implicit - they can however be handled by users thanks to **system execution adapters** *(described in [the "advanced features" chapter]{#chap_advfeats})*, allowing to code execution before and/or after the execution of a system's sub-tasks.



[^runtime_features]: ECST can be used to implement engine-level components and systems, while an additional data-driven library provides run-time flexibility and extensibility. Integration with ECST could be achieved by creating a "bridge" component that links entities between the two libraries.

[^explicit_locking_mechanisms]: some systems need to mutate a data structure during execution. Splitting them in separate subtasks requires *explicit locking* or a *thread-safe* data structure to avoid race conditions. It is often more efficient to simply run these systems in a single subtask.