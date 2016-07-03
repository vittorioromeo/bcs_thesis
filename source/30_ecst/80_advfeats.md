


# Advanced features {#chap_advfeats}
This chapter will cover the design and implementation of some less commonly used ECST features.



## Refresh event handling {#advf_refresh_event_handling}
The [refresh stage](#flow_refresh) takes care of various important operations, such as reclaiming dead entity IDs and subscribing/unsubscribing entities to systems. These operations produce *events* that can be optionally handled by the user through **refresh event handling**.

When calling the `context::step` method, a variadic number of functions can be passed that will be overloaded to *catch* refresh events and execute code:

```cpp
ctx.step([](auto& proxy){ /* ... */ },
    ecst::refresh_event::on_unsubscribe(st::s0,
        [](auto& instance, auto eid)
        {
            // Handle unsubscription of `eid` from `s::s0`.
        }),
    ecst::refresh_event::on_subscribe(st::s1,
        [](auto& instance, auto eid)
        {
            // Handle subscription of `eid` from `s::s1`.
        }),
    ecst::refresh_event::on_reclaim([](auto eid)
        {
            // Handle reclamation of `eid`.
        }));
```

### Implementation details
Refresh event handling is completely optional and implemented with compile-time function overloading: it does not introduce any additional unnecessary run-time overhead:

```cpp
template <typename TFStep, typename... TFsRefresh>
auto context::step(TFStep&& f_step, TFsRefresh&&... fs_refresh)
{
    // Creates the overload of refresh event handlers...
    auto refresh_event_handler =
        boost::hana::overload_linearly(fs_refresh...);

    ECST_SCOPE_GUARD([this, reh = std::move(refresh_event_handler)]
        {
            // ...and passes it to refresh.
            this->refresh(std::move(reh));
        });

    // ...
}
```

Every event has a unique type and `constexpr` variable:

```cpp
namespace impl
{
    struct subscribed_t { };
    struct unsubscribed_t { };
    struct reclaimed_t { };

    constexpr subscribed_t subscribed{};
    constexpr unsubscribed_t unsubscribed{};
    constexpr reclaimed_t reclaimed{};
}
```

Refresh implementation stages invoke the created overloaded function using the types defined above, in order to trigger the correct overload. Here's an example:

```cpp
void context::refresh_impl_kill_entities(
    TRefreshState& rs, TFRefresh&& f_refresh)
{
    // ...

    // Reclaim all dead entities and fire events.
    rs._to_kill.for_each([&](entity_id eid)
        {
            this->reclaim(eid);
            f_refresh(refresh_event::impl::reclaimed, eid);
        });

    // ...
}

```

The user interface functions return SFINAE-restricted lambdas that depend on the passed system tags:

```cpp
namespace refresh_event
{
    template <typename TSystemTag, typename TF>
    auto on_subscribe(TSystemTag, TF&& f)
    {
        return [f](impl::subscribed_t, auto& inst, auto eid)
            ->impl::enable_matching_instance<
                decltype(inst), TSystemTag>
        {
            return f(inst, eid);
        };
    }
}
```

The restriction allows to have multiple overloads that differ on the passed system tag, and is implemented as follows:

```cpp
template <typename TInstance, typename TSystemTag>
using enable_matching_instance =
    std::enable_if_t<check_tag<TInstance, TSystemTag>()>;
```

`impl::enable_matching_instance` is a type alias that makes use of `std::enable_if_t` *(see [@cppreference_enable_if])*, which prevents functions from participating in **overload resolution** *(see [@cppreference_overload_resolution])* if the `check_tag<TInstance, TSystemTag>()` expression evaluates to `false`. Here's the implementation of `check_tag`:

```cpp
// Returns `true` if `TInstance` is the system instance with
// tag `TSystemTag`.
template <typename TInstance, typename TSystemTag>
constexpr auto check_tag()
{
    // Retrieve system type from instance.
    using system_type = typename decay_t<TInstance>::system_type;

    // Create tag from retrieved system type.
    constexpr auto system_tag = tag::system::v<system_type>;

    // Check type equality between created and passed tags.
    return std::is_same<
        decay_t<decltype(system_tag)>,
        decay_t<TSystemTag>
        >{};
}
```



## System execution adapters
**System execution adapters** are used to define the *target systems* of user-defined *system processing functions* during a [step](#step_stage). Users can match zero or more systems depending on their tags or custom `constexpr` predicate functions. All systems can also be conveniently matched. Here's an example of system execution adapters in use:

```cpp
namespace sea = ecst::system_execution_adapter;

ctx.step([](auto& proxy)
    {
        proxy.execute_systems()(

            // Match systems `s::a` and `s::b`.
            sea::t(st::a, st::b)
                .for_subtasks([](auto& s, auto& data)
                    {
                        s.process_a(0, data);
                    }),

            // Match systems fulfilling `my_predicate`.
            sea::matching(my_predicate)
                .for_subtasks([](auto& s, auto& data)
                    {
                        s.process_b(1, data, 'a');
                    }),

            // Match remaining systems.
            sea::all()
                .for_subtasks([](auto& s, auto& data)
                    {
                        s.process_c(2, "test", data);
                    }));
    });
```

These constructs allow users to conveniently execute different processing functions *(that can have different interfaces)* on different systems.

### Implementation details
The implementation of system execution adapters is conceptually similar to the one for [refresh event handling](#advf_refresh_event_handling): all interface functions in the `system_execution_adapter` namespace will return SFINAE-restricted functions that will be linearly overloaded by the `proxy.execute_systems` call. The resultant function will then be called with every system during [system recursive task execution](#multithreading_recursive_task_execution) - only the matching overloads *(depending on tags or user-provided predicates)* will be invoked.

Every adapter is implemented using `system_execution_adapter::matching` as a building block:

* `system_execution_adapter::all` returns a `sea::matching` with a *tautology predicate*.

* `system_execution_adapter::t(...)` returns a `sea::matching` that uses a predicate very similar to the previously analyzed `check_tag` function to restrict systems depending on their tags.



## Entity handles

In order to **track** *particular entity instances*, users can create and manage **handles**. Handles are lightweight copyable objects *(usually as big as two pointers)* that can be used as parameters for functions provided by [defer proxies](#proxies_defer), [step proxies](#proxies_step) and by the context object:

```cpp
// Returns `true` if `h` is not a "null handle".
auto valid_handle(const handle& h) const;

// Returns the entity ID of the entity pointed by `h`.
// Asserts `valid_handle(h)`.
auto access(const handle&) const;

// Returns `true` if the entity pointed by `h` is alive.
// Asserts `valid_handle(h)`.
auto alive(const handle& h) const;
```

Handles can be used to safely check whether or not an entity was destroyed, even if its ID has been reused:

```cpp
auto e0 = context.create_entity();
auto h = context.create_handle(e);

// ...

if(context.alive(h))
{
    auto e1 = context.access(h);
}
```


### Implementation details

Handles are simple structs with two fields: the entity ID they're pointing to and a validity counter.

```cpp
struct handle
{
    entity_id _id;
    counter _ctr;
};
```

A special entity ID, equal to maximum finite value representable by the underlying numeric type, is the `invalid_id`. Handles pointing to `invalid_id` are considered **null** or **invalid** handles - `valid_handle` returns `false` for them.

Accessing entity metadata through an handle consists of the following steps:

* Check if the handle's counter is equal to the counter in the entity storage.

    * If the counter is not equal, the entity ID has been re-used and the handle points to a "dead" entity.

    * If the counter is equal, the corresponding metadata can be accessed through the handle's stored ID.

![ECST advanced features: accessing entity metadata through handle](source/figures/handle.png){#handlepic width=80% }