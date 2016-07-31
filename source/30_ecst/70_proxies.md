


# Proxy objects {#chap_proxies}

**Proxy objects** are used to provide the user with a *restricted interface* that increases the safety and readability of application code. Proxy objects are instantiated by ECST and passed as a reference in the following cases:

* During entity processing in systems, a **data proxy** object is used to access *component data* and *previous system outputs*.

    * Data proxies also give access to *deferred function* creation, which is done through **defer proxy** objects. Defer proxies allow the user to enqueue *critical operations* in a context where only non-critical operations can be executed.

* In order to immediately execute *critical operations* or begin *system chain execution*, a **step proxy** object must be used. Step proxies are created from the context and accessed through the `context::step` method.

    * **Executor proxy** objects are required to access *system processing functions* during system chain execution *(inside of a **step**)*. They are usually hidden behind more convenient abstractions provided by *system execution adapters*.

All proxies are implemented as template classes containing `private` callable objects *(and additional data)*, with a `public` interface that invokes the stored callables.


## Data proxies {#dddata_proxy}

**Data proxies** are created during [*inner parallelism slicing*](#inner_par_slicing). Every data proxy is bound to a particular [*subtask state*](#storage_state) and provides the following interface functions:

* Entity iteration:

    ```cpp
    // Iterates over entities assigned to the current subtask.
    template <typename TF>
    auto for_entities(TF&& f);

    // Iterates over all entities in the system.
    template <typename TF>
    auto for_all_entities(TF&& f);

    // Iterates over all entities not in the current subtask.
    template <typename TF>
    auto for_other_entities(TF&& f);
    ```

* Entity count:

    ```cpp
    // Count of entities of the current subtask.
    auto entity_count() const;

    // Count of all entities in the system.
    auto all_entity_count() const;

    // Count of entities not in the current subtask.
    auto other_entity_count() const;
    ```

* Entity/component manipulation:

    ```cpp
    // Returns a reference to a component of `eid` with tag `ct`.
    template <typename TComponentTag>
    decltype(auto) get(TComponentTag ct, entity_id eid);

    // Enqueues a "deferred function".
    template <typename TF>
    void defer(TF&& f);

    // Marks an entity as "dead".
    void kill_entity(entity_id eid);
    ```

* System output access:

    ```cpp
    // Returns a reference to the system's output data.
    auto& output();

    // Loops over the outputs of a previous system (dependency).
    template <typename TSystemTag, typename TF>
    decltype(auto) for_previous_outputs(TSystemTag st, TF&& f);
    ```

Data proxies begin their life during the definition of system processing overloads *(in a **step**)*:

```cpp
ctx.step([&](auto& proxy)
    {
        proxy.execute_systems_from(st::s0, st::s1)(
            sea::t(st::s0).for_subtasks([](auto& s, auto& data)
                {
                    s.process(data);
                }),
            sea::t(st::s1).for_subtasks([](auto& s, auto& data)
                {
                    s.process(data);
                }));
    });
```

The `data` arguments shown above are created during [*inner parallelism slicing*](#inner_par_slicing) and automatically passed to the overloaded processing functions by the context. The system implementation can then access data proxies as follows:

```cpp
struct s0
{
    template<typename TData>
    void process(TData& data)
    {
        data.for_entities([](auto eid){ /* ... */ });
    }
};
```


### Defer proxies {#proxies_defer}

**Defer proxies** are created by data proxies and can only be accessed through them. They provide an interface to enqueue critical operations that will be executed during a [*refresh*](#flow_refresh):

* Entity/handle manipulation:

    ```cpp
    entity_id create_entity();
    void kill_entity(entity_id);

    handle create_handle(entity_id);
    handle create_entity_and_handle();
    auto valid_handle(const handle& h) const;
    auto access(const handle&) const;
    ```

* Component access/manipulation:

    ```cpp
    template <typename TComponentTag>
    decltype(auto) add_component(TComponentTag, entity_id);

    template <typename TComponentTag>
    decltype(auto) get_component(TComponentTag, entity_id);

    template <typename TComponentTag>
    void remove_component(TComponentTag, entity_id);
    ```

* System access:

    ```cpp
    template <typename TSystemTag>
    auto& instance(TSystemTag);

    template <typename TSystemTag>
    auto& system(TSystemTag);

    template <typename TSystemTag, typename TF>
    decltype(auto) for_system_outputs(TSystemTag, TF&& f);
    ```

Here is an example of a defer proxy in use:

```cpp
data.for_entities([&](auto eid)
    {
        data.defer([&](auto& proxy)
            {
                auto e = proxy.create_entity();
                proxy.add_component(ct::c0, e);
            });
    });
```

The enqueued operations will be executed at the end of a [*step*](#step_stage), during the automatically-triggered [refresh *"execute deferred functions"* phase](#flow_exec_dfuncs).



## Step proxies {#proxies_step}

**Step proxies** allow every operation that [*defer proxies*](#proxies_defer) do, in addition to functions which *begin system chain execution*:

```cpp
// Executes all system chains starting from `sts...`.
template <typename... TStartSystemTags>
auto execute_systems_from(TStartSystemTags... sts);

// Executes all system chains.
auto execute_systems();
```

These functions are accessed through the `context::step` method, which creates a step proxy and passes it to an user-defined function. The method also accepts a variadic number of `fs_refresh...` refresh event handler functions: the feature will be covered in [Chapter 12, Section 12.1](#chap_advfeats).

```cpp
template <typename TFStep, typename... TFsRefresh>
auto context::step(TFStep&& f_step, TFsRefresh&&... fs_refresh)
{
    auto refresh_event_handler =
        boost::hana::overload_linearly(fs_refresh...);

    // Ensure `refresh()` is automatically called after executing `f`.
    ECST_SCOPE_GUARD([this, reh = std::move(refresh_event_handler)]
        {
            this->refresh(std::move(reh));
        });

    // Clear refresh state.
    _refresh_state.clear();

    // Build context step proxy.
    step_proxy_type step_proxy{*this, _refresh_state};

    // Execute user-defined step.
    return f_step(step_proxy);
}
```

Here is an example usage of a step proxy:

```cpp
ctx.step([&](auto& proxy)
    {
        proxy.execute_systems()(
            sea::all().for_subtasks([](auto& s, auto& data)
                {
                    s.process(data);
                }));
    },
    ecst::refresh_event::on_unsubscribe(st::s0,
        [](s::s0& system, entity_id eid){ /* ... */ }));
```



### Executor proxies

**Executor proxies** are created from *system instances* and used to execute system processing functions. They allow more fine-grained control over system execution and can only be accessed in a *step*, using the `.detailed` method of any *system execution adapter*. Here's a usage example:

```cpp
ctx.step([](auto& proxy)
    {
        proxy.execute_systems()(
            sea::all().detailed([&](auto& system, auto& executor)
                {
                    // Code to run before execution.

                    executor.for_subtasks([&](auto& data)
                        {
                            // Code that runs in every subtask.
                            system.process(data);
                        });

                    // Code to run after execution.
                }));
    });
```

Normally, executor proxies are hidden behind the more convenient *(yet more limited)* *system execution adapter* `.for_subtasks` method interface.