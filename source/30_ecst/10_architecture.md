


# Architecture

Before analyzing the code and techniques used to implement ECST, the architecture of the library will be examined.

A very high-level view of ECST's architecture can be illustrated as such:

\dot(source/figures/generated/ecst/architecture/high_level { width=75% })
(ECST architecture: high-level overview)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    Context [shape="diamond"]
    User -> Context [dir="both"]

    "Thread Pool" [shape="rectangle"]
    "Systems" [shape="rectangle"]
    "Component Data" [shape="rectangle"]
    "Entity Metadata" [shape="rectangle"]

    subgraph cluster_context
    {
        Context -> "Thread Pool" [dir="both"]
        Context -> "Systems" [dir="both"]
        Context -> "Component Data" [dir="both"]
        Context -> "Entity Metadata" [dir="both"]
    }
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By looking at the diagram, it is obvious that the roles of the context are:

* Providing a **friendly interface** between the user and the library.

* **Decoupling** entities, components, and systems.

## Context

In the current version of the library, the `context` stores entity, system and component data.

* The composition of the **entity metadata storage** and of the **component data storage** is called `main_storage`.

* The element managing systems, threads, and scheduling is called the `system_manager`.

\uml(source/figures/generated/ecst/architecture/context_aggregation { width=80% })
(ECST architecture: context)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

context *-- "1" main_storage
context *-- "1" system_manager

main_storage *-- "1" component_data_storage
main_storage *-- "1" entity_metadata_storage

system_manager *-- "1" system_storage
system_manager *-- "1" thread_pool
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Entity metadata storage

The **entity metadata storage** contains `metadata` instances for every entity, which are used to:

* Keep track of the component types an entity possesses.

* Map entities to handles and check their validity.

It also manages unused and used entity IDs.

\uml(source/figures/generated/ecst/architecture/entity_metadata_storage { width=75% })
(ECST architecture: entity metadata storage)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

left to right direction

class entity_metadata_storage {
    sparse_int_set _free_ids
    metadata[] _metadata

    entity_id create()
    void reclaim(entity_id)
    bool alive(entity_id)
    metadata& get_metadata(entity_id)
}

class metadata {
    bitset _component_type_bits
    size_t _validity_counter
}

entity_metadata_storage o-- "many" metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

<!-- * -->



### Component data storage

The **component data storage** contains `chunk` instances for every component signature type. **Chunks** store the data of one or more component types with a user-specified strategy *(e.g. contiguous buffer or hash map)* and provide a way to retrieve references to component data given entity IDs.


\uml(source/figures/generated/ecst/architecture/component_data_storage { width=85% })
(ECST architecture: component data storage)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

left to right direction

class component_data_storage {
    chunk[] _chunk
}

class chunk {
    container _data

    auto& get(entity_id)
}

component_data_storage o-- "many" chunk

chunk *-- "1" container

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

<!-- * -->



### System manager {#architecture_system_mgr}

The system manager contains:

* A `thread_pool` instance, used to efficiently execute system logic in separate threads.

* A `system_storage`, which stores an `instance` for every system signature type.

    * **Instances** store an instance of the user-provided system type and system metadata.

\uml(source/figures/generated/ecst/architecture/system_manager { width=85% })
(ECST architecture: system manager)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

left to right direction

class system_manager {
    thread_pool _thread_pool
    system_storage _system_storage
}

class system_storage {
    instance[] _instances
}

system_manager *-- "1" thread_pool
system_manager *-- "1" system_storage

system_storage o-- "many" instance

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

<!-- * -->



#### Instances

Instances wrap user-provided systems, storing an instance of the "real" system type and additional metadata:

* A `state_manager`, containing `state` instances.

    * Every subtask executed by an `instance` has its own `state`, which contains eventual *system output*, *deferred functions*[^deferred_functions], and IDs of entities to reclaim.

* A *sparse integer set*[^sparse_set] tracking the entity IDs subscribed to the instance.

* A *dense bitset*[^dense_bitset] representing the set of component types required for system subscription.


\uml(source/figures/generated/ecst/architecture/instance)
(ECST architecture: system instance)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
\plantuml_style

left to right direction

class instance {
    state_manager _state_manager
    system _system
    sparse_int_set _subscribed
    bitset _required
}

class state_manager {
    state[] _states
}

class state {
    sparse_int_set _to_reclaim
    output _output
    function[] _deferred_functions
}

instance *-- "1" state_manager
instance *-- "1" system

state_manager o-- "many" state

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


<!-- * -->



[^deferred_functions]: used to delay the execution of functions in a later synchronous step.

[^sparse_set]: "sparse integer sets" are very efficient data structures for the management of entity IDs. They are covered in [the "miscellaneous" chapter](#appendix_sparse_integer_sets).

[^dense_bitset]: `std::bitset`.