


## Data-oriented composition

In order to make the most of a machine's hardware, a major development paradigm shift has to be taken: enter **data-oriented design**. DOD is *all about the data*: code **has to be designed around the data** and not vice-versa. When used correctly, data-oriented design can allow applications to take advantage of parallelism and a higher percentage of cache hits. Additional benefits include modularity, easier networking, and easier serialization.

To achieve all the aforementioned advantages, the following design will be used:

* Entity instances will be simple **numerical IDs**.

* **Component types** will be simple, small and logic-less.

* Component data will be **stored separately** from entities.

* Logic will be separately handled by **systems**.

    * Entities will subscribe to systems depending on their current active component types.

* A **context** *(manager)* object will **tie everything together**.

    * The various parts of the pattern will communicate with each other and with the user through the context.

An intuition for this technique is thinking about **relational database management systems** *(RDBMSs)* tables, with component types as columns, and entity instances as rows:

|           | ComponentA | ComponentB | ComponentC |
|-----------|:----------:|:----------:|:----------:|
| Entity #0 |      X     |      X     |            |
| Entity #1 |            |      X     |            |
| Entity #2 |      X     |            |      X     |

The table above shows how component types can be bound and unbound from entity instances. The previously mentioned **context** object will keep track of component availability in entity instances, providing an interface roughly similar to `bool context::has_component<...>(entity_id)`.

\uml(source/figures/generated/ecs/overview/dod_composition/uml_context_has_component { width=65% })
(DOD: checking component type availability through context object)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

User -> context: `has_component(...)`
context -> "entity metadata"
"entity metadata" --> context
context --> User: `true` or `false`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Knowing that an entity instance possesses a specific component type, a function that retrieves the data of the component for that particular instance will also be provided by the context object: `auto& context::get_component<...>(entity_id)`.

\uml(source/figures/generated/ecs/overview/dod_composition/uml_context_get_component { width=65% })
(DOD: getting component instance data through context object)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

User -> context: `get_component(...)`
context -> "component storage"
"component storage" --> context
context --> User: reference to component data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The role of `entity metadata` and `component storage` in the diagrams is to show the additional layer of abstraction between the user and the pattern implementation. With the introduction of the **context object** concept, it is possible to cleanly implement **systems**. They will "ask" the context to return the set of all matching entities[^return_set_of_matching_entities], with an interface like `void context::for_entities_with<...>(f)`.

\uml(source/figures/generated/ecs/overview/dod_composition/uml_context_for_entities_with { width=75% })
(DOD: retrieving entities matching a component type set through context object)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

User -> context: `for_entities_with(...)`
context -> cache
cache -[#0000FF]> "entity metadata": [if not cached]
"entity metadata" -[#0000FF]-> cache
cache --> context
context --> User: higher-order processing function
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a user-code example system implementation:

```cpp
void example_system(context& c)
{
    c.for_entities_with<a_type, c_type>([&c](auto eid)
        {
            auto& a_data = c.get_component<a_type>(eid);
            auto& c_data = c.get_component<c_type>(eid);

            perform_action(a_data, c_data);
        });
}
```

All the logic of the application can then be defined in terms of sequential data transformations[^dataflow_programming], which are very easy to maintain, expand and parallelize. For instance, `example_system` could be parallelized by splitting the range provided by `for_entities_with` evenly between CPU cores.

The role of the context is to decouple entities, components and systems, and provide a high level of abstraction. Component data could be stored in *arrays*, *hash tables*, or even on another machine over the network.

\dot(source/figures/generated/ecs/overview/dod_composition/context_role { width=75% })
(DOD: role of the context object)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    dispatch [shape="diamond"]
    context [shape="rectangle"]
    network [style="dashed"]


    user -> context [dir="both"]
    context -> entity_metadata [dir="both"]
    context -> component_storage [dir="both"]
    component_storage -> dispatch [dir="both"]

    subgraph
    {

        dispatch -> network [dir="both", style="dashed"]
        dispatch -> hash_map [dir="both"]
        dispatch -> array [dir="both"]
    }
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


### Implementation

There are some implementation details inherently related to the approach. Since entities are numerical IDs, it is sufficient to define a type alias:

```cpp
using entity_id = std::size_t;
```

If all component types and system types are supposed to be known at compile-time, it is unnecessary to define base classes for them. Implementing component storage can be done in multiple ways: the most simple and straightforward way is using a separate array per component type:

```cpp
struct component_a { /* ... */ };
struct component_b { /* ... */ };
struct component_c { /* ... */ };

constexpr auto max_entities{10000};

class component_storage
{
private:
    std::array<component_a, max_entities> _a;
    std::array<component_b, max_entities> _b;
    std::array<component_c, max_entities> _c;

public:
    template <typename TComponent>
    TComponent& get(entity_id eid);
};
```

The `context` will take care of retrieving data from `component_storage`, making the implementation of system types extremely simple:

```cpp
struct system_ac
{
    void process(context& c)
    {
        c.for_entities_with<a_type, c_type>([&c](auto eid)
            {
                 /* ... */
            });
    }
};
```

The application code will roughly look like this:

```cpp
int main()
{
    component_storage cs;
    context c{cs};

    system_ac s_ac;

    // ...create entities...
    // ...add components...

    while(running)
    {
        s_ac.process(c);
    }
}
```

All the leftover details can be implemented in multiple ways:

* Components can be bound to entities by using a **dense bitset**, where every bit corresponds to a component type.

    * The bitsets and additional metadata can be stored in various ways - the `context` will take care of providing access to them.

* Systems can keep track of the subscribed entities by storing their IDs in an appropriate data structures.

    * The `context` can take care of matching entities to systems when a new entity is created or its components are changed.

* Components and entities can communicate with each other by allowing systems to produce outputs that can be processed by the application code.



#### Role-playing game

The class design is identical to the one seen in the object-oriented composition approach. Instead of using `behavior` types that handle both data and logic, they are completely split: data is stored in components, logic is handled by systems:

```cpp
// The namespace `c` will contain all component types.
namespace c
{
    struct physics { /* ... */ };
    struct ai { /* ... */ };
    struct npc { /* ... */ };
    struct flight { /* ... */ };
    struct sword { /* ... */ };
    struct bow { /* ... */ };
}

// The namespace `s` will contain all system types.
namespace s
{
    // Processes entities with `c::physics`.
    struct physics { /* ... */ };

    // Processes entities with `c::ai` and `c::npc`.
    struct ai_npc { /* ... */ };

    // ...
}
```

Entity creation and mutation are delegated to the `context`, which takes care of bookkeeping and of binding all elements together:

```cpp
auto make_skeleton(context& c, /* ... */)
{
    auto eid = c.create_entity();
    c.emplace_component<physics>(eid, /* ... */);
    c.emplace_component<ai>(eid, /* ... */);
    c.emplace_component<npc>(eid, /* ... */);

    return eid;
}
```

The application code or the `context` will take care of instantiating and executing systems. Systems that do not depend on each other can be executed in parallel, and systems with no processing ordering requirements can also be internally parallelized.

#### GUI framework

The data-oriented implementation of the example GUI framework is conceptually identically to the RPG one. A powerful benefit of using systems to handle logic is that animation features are cleanly handled and specialized for every widget type:

```cpp
namespace c
{
    struct animation { /* ... */ };
    struct layout { /* ... */ };
    struct keyboard { /* ... */ };
    struct mouse { /* ... */ };

    // Sometimes highly-specific components can be
    // defined to handle particular situations or to
    // simply "tag" entities.
    struct textbox { /* ... */ };
    struct button { /* ... */ };
}

namespace s
{
    // Processes entities with `c::textbox` and `c::keyboard`.
    struct textbox { /* ... */ };

    // Processes entities with `c::button` and `c::mouse`.
    struct button { /* ... */ };

    // Textbox-specific optional animations.
    // Processes entities with `c::textbox` and `c::animation`.
    struct anim_textbox { /* ... */ };

    // Button-specific optional animations.
    // Processes entities with `c::button` and `c::animation`.
    struct anim_button { /* ... */ };
}
```

As seen from the above component and system definitions, the existence of an `animation` component in an entity will either enable or disable optional animations. If an entity has the `animation` component, the logic will depend on the other components the entity has, making it easy to define widget-specific animation behavior.

All that's left is instantiating the `context` and the system types, then execute application-specific logic:

```cpp
int main()
{
    context c;

    s::textbox s_textbox;
    s::button s_button;
    s::anim_textbox s_anim_textbox;
    s::anim_button s_anim_button;

    // ...create entities and components...

    while(running)
    {
        s_textbox.process(c);
        s_button.process(c);
        s_anim_textbox.process(c);
        s_anim_button.process(c);
    }
}
```

The boilerplate code shown in the code snippet above can be avoided by using advanced metaprogramming techniques. In [part 2](#part2_ecst), the way **ECST** avoids similar bookkeeping code will be analyzed.

### Communication

#### Inter-component

Systems elegantly solve the problem of inter-component communication. Imagine a simple physics simulation using the following components:

```cpp
struct position { vec3f _v };
struct velocity { vec3f _v };
struct acceleration { vec3f _v };
```

Two systems can be used to implement $v' = v + a$ and $p' = p + v$, allowing `velocity` to communicate with `acceleration` and `position` to communicate with `velocity`:

```cpp
void process_acceleration(context& c)
{
    c.for_entities_with<velocity, acceleration>([&c](auto eid)
        {
            c.get_component<velocity>(eid)._v +=
                c.get_component<acceleration>(eid)._v;
        });
}

void process_velocity(context& c)
{
    c.for_entities_with<position, velocity>([&c](auto eid)
        {
            c.get_component<position>(eid)._v +=
                c.get_component<velocity>(eid)._v;
        });
};
```

#### Inter-system {#sys_streamqueue}

Inter-system communication can also be very useful. Consider situations where multiple system dependency chains run in parallel: some systems may require forwarding information to the next system in the chain.

There are various ways of solving this problem:

* Systems could be stateful *(storing their outputs, so that others can access them)* and could store references to other systems. Particular care must be used in making sure that a system has finished processing before accessing its output and that its memory location does not change.

    \dot(source/figures/generated/ecs/overview/dod_composition/output_system_communication { width=55% })
    (DOD communication: example stateful system communication architecture)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    digraph
    {
        rankdir=LR

        Consumer0 [label="Consumer"]
        Consumer1 [label="Consumer"]
        Output [shape="cylinder"]

        subgraph cluster_producer
        {
            color="black"

            Producer
            Output
        }

        Producer -> Consumer0
        Producer -> Consumer1

        Output -> Consumer0 [style=dotted, arrowhead="onormal"]
        Output -> Consumer1 [style=dotted, arrowhead="onormal"]
    }
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* A **streaming** technique using queues could be used in certain situations *(depending on the implementation of the systems)* - one system would act as a *producer* and other systems would act as *consumers*. The producer system would enqueue messages during entity processing - other systems would not directly process entities, instead process received messages.

    \dot(source/figures/generated/ecs/overview/dod_composition/queue_system_communication { width=70% })
    (DOD communication: example streaming system communication architecture)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    digraph
    {
        rankdir=LR

        Queue [shape="record", label="{* | * | * | *}"]

        Consumer0 [label="Consumer"]
        Consumer1 [label="Consumer"]

        Producer -> Queue
        Queue -> Consumer0
        Queue -> Consumer1
    }
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#### Inter-entity

Inter-entity communication isn't as useful as in the previous encoding techniques, but some particular situations may require specific entity instances to share data. *"Inter-entity"* is a misnomer, as logic-less entities cannot directly communicate together - specialized systems will have to initiate and resolve inter-entity messages. This can be achieved in multiple ways:

* Systems can produce special outputs containing the IDs of the entities that intend to communicate and a particular message. Subsequent systems will take care of processing those outputs and performing actions depending on the type/contents of the messages.

* A thread-safe queue can be accessed by systems during execution to enqueue messages. Subsequent systems can sequentially dequeue all messages and directly act upon entity instances depending on the type/contents of the messages.

Having two tightly coupled entity instances when using the Entity-Component-System pattern is a red flag: it's very likely that the coupling can be avoided by introducing new components and/or systems, or by modifying the design of the application.


### Advantages and disadvantages

Using data-oriented composition, all the benefits of object-oriented composition are maintained, but several new advantages are achieved:

* Data and logic **are separated**.

* The code becomes **more modular**, easier to maintain and extend.

* Entities are more easily **serializable** and **synchronizable** over the network.

* Entities can be processed in terms of **chained data transformations**, allowing parallelization and cache-friendliness.

* No unnecessary run-time polymorphism overhead.

One *perceived* disadvantage may be that the code is harder to reason about compared to an object-oriented approach, and inherently less abstracted. One of the objectives of this thesis is showing that, with a proper ECS library, the code is **actually easier to reason about** *(thanks to a dataflow-oriented approach)* and that high-level abstractions *(and the safety/convenience they provide)* do **not have to be sacrificed**.

In addition, data-oriented composition lends itself very nicely to multi-machine parallel computing - a real-world example is Improbable's **SpatialOS** cloud-based architecture [@spatialos_learnmore], which massively parallelizes computation in a transparent way using a variant of the Entity-Component-System pattern.



[^return_set_of_matching_entities]: in a real implementation, systems will efficiently cache the set of entities they match - the `context` will not have to continuously iterate over all existing entities.

[^dataflow_programming]: "dataflow programming".
