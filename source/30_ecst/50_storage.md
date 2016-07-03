


# Storage

ECST stores **entity metadata**, **component data**, and **system instances** inside the context object. To optimize performance depending on user-defined settings, *static dispatching* *(see [the "miscellaneous" chapter](#appendix_static_dispatching))* techniques are used. This chapter will cover the design and implementation of the aforementioned storage types.



## Component data {#storage_component}

Component data is stored in **chunks**. A **chunk** binds one or more component types to a particular **component storage strategy**. When the user tries to access a component by a tag `ct`, the chunk responsible for storing `ct` is found at compile-time, and the data is retrieved from the bound storage.

Chunks are stored inside the context in a [`boost::hana::tuple`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1tuple.html).



### Component storage strategy {#storage_comp_strategy}

A **component storage strategy** is a class designed to store component data. Any class can be used as a storage strategy, as long as it satisfies the following requirements:

* It needs to provide two nested type names:

    * `component_tag_list_type`: a *type list* containing all the tags of components stored.

    * `metadata_type`: storage-specific metadata that will be *injected* in entity metadata. Can be used to store additional data required to retrieve components directly in the entities. Usually an empty class.

* It needs to implement the following interface:

    ```cpp
    // Given a component tag, an entity ID and its
    // storage-specific metadata, returns a reference to
    // the corresponding component.
    template <typename TComponentTag, typename... Ts>
    auto& get(TComponentTag, entity_id, const metadata_type&);

    // Given a component tag, an entity ID and its
    // storage-specific metadata, creates a component and
    // returns a reference to it.
    template <typename TComponentTag, typename... Ts>
    auto& add(TComponentTag, entity_id, metadata_type&);
    ```

By default, the `contiguous_buffer`, `empty` and `hash_map` storage strategies are available.

* `contiguous_buffer` stores data in either an `std::array` or an `std::vector`, depending on whether or not the *entity limit* is fixed or dynamic.

* `empty` does not store any data - it's used for data-less components which only "mark" entities.

* `hash_map` stores data in an `std::unordered_map`. It should only be used for very big components with infrequent lookups/additions.

Users can create their own storage strategies by writing classes fulfilling the requirements mentioned above, and by providing a *"maker"* `struct` with the following interface:

```cpp
template <typename TComponentTagList>
struct my_storage_strategy { /* ... */ };

struct my_storage_strategy_maker
{
    // Given context settings and a list of component tags, return
    // an `mp::type_c` wrapping the appropriate storage strategy.
    template <typename TSettings, typename TComponentTagList>
    constexpr auto make_type(TSettings, TComponentTagList) const

    {
        // Static dispatching that depends on `TSettings` and
        // `TComponentTagList` can be performed here to improve
        // performance and memory usage.

        return mp::type_c</* ... */>;
    }
};
```

The newly created class can then be used during component signature definition:

```cpp
constexpr auto cs_test_component =
    cs::make(ct::test_component)
        .storage_strategy(my_storage_strategy_maker{});
```

Several component storage strategy designs have been analyzed in depth by Adam Martin [@tmachine_compstorage].



## Entity metadata {#storage_entity}
**Entity metadata** can be accessed through entity IDs and deals with keeping track of active components, ensuring handle validity and storing *chunk metadata*.

It is implemented as a simple `struct`:

```cpp
template <typename TComponentBitset, typename TChunkMetadataTuple>
struct metadata : TChunkMetadataTuple
{
    TComponentBitset _bitset;
    counter _counter;
    // ...
};
```

`metadata` derives from `TChunkMetadataTuple` in order to take advantage of the **empty base optimization** *(EBO)* *(more details at [@cppreference_ebo])*. The stored `_counter` is incremented every time an entity IDs is reused - handles that try to access an entity check if their local counter matches with `_counter` to make sure they're not accessing another entity reusing the same ID [@tmachine_eids].

All entity metadata instances, along with available entity IDs, are stored in either `ecst::entity::container::dynamic` or `ecst::entity::container::fixed`, depending on the entity limit specified by the user in context settings.

The dynamic storage uses an `std::vector` to store metadata and a *dynamic sparse integer set* to store available IDs. The fixed storage uses an `std::array` to store metadata and a *fixed sparse integer set* to store available IDs - it is faster than the dynamic one as no checks for growth *(reallocation)* have to be performed.

**Sparse integer sets** are data structures extremely efficient for the management of entity IDs. They are analyzed in [the "miscellaneous" chapter](#appendix_sparse_integer_sets).



## Instances and systems {#storage_system}

User-defined systems are stored inside **system instances**. Every system type has a corresponding system instance. All system instances are stored in the context, in an `std::tuple`, allowing users and other modules of the library to lookup instances at compile-time by system type.



### Instance
A **system instance** is composed of the following members:

* An instance of the user-defined system type - systems can be stateful *(e.g. for caching reasons or to store a data structure)* and may require storage.

* A [*sparse integer set*](#appendix_sparse_integer_sets) of the currently subscribed entity IDs.

* A *dense bitset* of the component types required for system subscription *(see [the "miscellaneous" chapter](#appendix_component_bitset_creation) for details)*.

* A [**parallel executor**](#multithreading_par_executor) object that implements [*inner parallelism*](#multithreading_inner_par).

* A **state manager** object that binds a **state** to every *subtask*.

#### State {#storage_state}

Every *subtask* has a corresponding **state**, which stores the following elements:

* *Output data* optionally generated from the subtask.

    * The data is set during subtask execution.

    * The data can be read from dependent systems or during a *step*.

* A `to_kill` sparse integer set, that keeps track of the entities marked as dead during subtask execution.

    * The set is filled during subtask execution.

    * The entities are reclaimed during a *refresh*.

* An `std::vector` of **deferred functions**.

    * The vector is filled during subtask execution.

    * The functions are sequentially executed during a *refresh*.


