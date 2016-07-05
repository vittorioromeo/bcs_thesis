


# Compile-time settings {#chap_ecst_compiletime}

After including ECST, the user must define some mandatory compile-time settings, required to instantiate a `context`:

\uml(source/figures/generated/ecst/compiletime/options_activity)
(ECST compile-time settings: mandatory options)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style
left to right direction

(*) --> "Define tags"
--> "Define signatures"
--> "Define context settings"
--> "Instantiate `context`"
--> (*)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

<!-- * -->

Tag definition was previously described in [Chapter 6, Section 6.2](#metaprogramming_tags). **Signatures** and **context settings** will be covered in the following sections.



## Signatures

**Signatures** are `constexpr` values containing compile-time options. They are implemented using option maps, covered in [Chapter 6, Section 6.3](#metaprogramming_option_maps). There are two kinds of signatures: **component signatures** and **system signatures**.

### Component signatures

**Component signatures** are used to *bind* storage strategies with component types. Multiple component tags can be bound to a specific storage strategy. Users can implement their own storage strategies *(briefly explained in [Chapter 9, Subsection 9.1.1](#storage_comp_strategy))*. The `contiguous_buffer` strategy is available by default and allows users to store components in contiguous memory locations.

#### SoA

Creating a `contiguous_buffer` signature per component type results in a **SoA** *(structure of arrays)* storage layout:

```cpp
namespace cs = ecst::signature::component;

constexpr auto cs_acceleration =
    cs::make(ct::acceleration).contiguous_buffer();

constexpr auto cs_velocity =
    cs::make(ct::velocity).contiguous_buffer();

constexpr auto cs_position =
    cs::make(ct::position).contiguous_buffer();
```

\dot(source/figures/generated/ecst/compiletime/soa_layout)
(ECST compile-time settings: high-level view of SoA component storage layout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    subgraph cluster_z
    {
        label="acceleration"
        C [shape="record", rank=-10000, label="A | <f1> A | A | A | A | ..."]
        C
    }

    subgraph cluster_y
    {
        label="velocity"
        B [shape="record", rank=-10000, label="V | <f1> V | V | V | V | ..."]
        B
    }

    subgraph cluster_x
    {
        label="position"
        A [shape="record", rank=-10000, label="P | <f1> P | P | P | P | ..."]
        A
    }

    1 [label="EID: 1"]

    C:f1 -> 1 [dir="back"]
    B:f1 -> 1 [dir="back"]
    A:f1 -> 1 [dir="back"]
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


#### AoS

Creating a `contiguous_buffer` signature with multiple component types results in a **AoS** *(array of structures)* storage layout:

```cpp
constexpr auto cs_physics = signature::component::make(
    ct::acceleration, ct::velocity, ct::position)
        .contiguous_buffer();
```
\dot(source/figures/generated/ecst/compiletime/aos_layout { width=75% })
(ECST compile-time settings: high-level view of AoS component storage layout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    subgraph cluster_x
    {
        label="physics"
        A [shape="rectangle",  label=<
            <TABLE ALIGN="LEFT" BORDER="0">
                <TR>
                    <TD BORDER="1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR>
                                <TD BORDER="1">A</TD>
                                <TD BORDER="1">V</TD>
                                <TD BORDER="1">P</TD>
                            </TR>
                        </TABLE>
                    </TD>
                   <TD BORDER="1" PORT="f1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR >
                                <TD BORDER="1">A</TD>
                                <TD BORDER="1" >V</TD>
                                <TD BORDER="1">P</TD>
                            </TR>
                        </TABLE>
                    </TD>
                    <TD BORDER="1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR>
                                <TD BORDER="1">A</TD>
                                <TD BORDER="1">V</TD>
                                <TD BORDER="1">P</TD>
                            </TR>
                        </TABLE>
                    </TD>
                    <TD BORDER="1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR>
                                <TD BORDER="1">A</TD>
                                <TD BORDER="1">V</TD>
                                <TD BORDER="1">P</TD>
                            </TR>
                        </TABLE>
                    </TD>
                    <TD BORDER="1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR>
                                <TD BORDER="1">A</TD>
                                <TD BORDER="1">V</TD>
                                <TD BORDER="1">P</TD>
                            </TR>
                        </TABLE>
                    </TD>
                    <TD BORDER="1">
                        <TABLE ALIGN="LEFT" BORDER="0">
                            <TR>
                                <TD BORDER="1">...</TD>
                            </TR>
                        </TABLE>
                    </TD>
                </TR>
            </TABLE>
        >, ];
    }

    1 [label="EID: 1"]

    A:f1 -> 1 [dir="back"]
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



### System signatures {#system_sigs}

**System signatures** are used to define the following system settings:

* **Inner parallelism policy**: either allows the system to run in multiple threads *(subtasks)* using a specific strategy or forces the system to run in a single thread;

* **List of dependencies**: list of systems whose execution needs to be completed before allowing the current one to run. Used to build the [previously mentioned](#overview_outer_parallelism_dag) outer parallelism DAG;

* **Accessed component types**: components types mutated or read by the system. Used to subscribe matching entities to the system and to allow and verify component access in system implementation;

* **Output type**: type of data produced by every subtask, if any.

An example of a system signature definition is given below:

```cpp
constexpr auto ss_collision =
    signature::system::make(st::collision)
        .parallelism(split_evenly_per_core)
        .dependencies(st::spatial_partition)
        .read(ct::circle)
        .write(ct::position, ct::velocity)
        .output(ss::output<std::vector<contact>>);
```



### Signature lists {#ctopts_siglist}

**Signature lists** are compile-time lists of system signatures, that are used to group all defined component signatures and system signatures together, in order to pass them to the context settings definition.

They are implemented using [`boost::hana::basic_tuple`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1basic__tuple.html). The user creates them using the following syntax:

```cpp
constexpr auto make_csl()
{
    constexpr auto cs_acceleration = /* ... */;
    constexpr auto cs_velocity = /* ... */;
    constexpr auto cs_position = /* ... */;

    return signature_list::component::make(
        cs_acceleration, cs_velocity, cs_position
        );
}

constexpr auto make_ssl()
{
    constexpr auto ss_acceleration = /* ... */;
    constexpr auto ss_velocity = /* ... */;
    constexpr auto ss_collision = /* ... */;

    return signature_list::system::make(
        ss_acceleration, ss_velocity, ss_collision
        );
}
```



## Context settings

**Context settings** are mandatory options that need to be defined prior to `context` instantiation, implemented using [option maps](#metaprogramming_option_maps). The context needs to be aware of:

* All the previously defined *component signatures*, and *system signatures*. These will be passed to the settings as *signature lists*;

* The chosen **multithreading policy** and **system scheduling strategy**;

* The desired **entity storage policy**, which can be *dynamic* or *fixed*.

    * Entity and component insertion will be faster with a fixed limit, as no checks for possible reallocations are required.

Here is an example context settings definition and context instantiation:

```cpp
constexpr auto context_settings =
    ecst::settings::make()
        .allow_inner_parallelism()
        .fixed_entity_limit(ecst::sz_v<10000>)
        .component_signatures(make_csl())
        .system_signatures(make_ssl());

auto context = ecst::context::make(context_settings);
```