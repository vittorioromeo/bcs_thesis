


# Metaprogramming {#chap_ecst_metaprogramming}

Before diving into Entity-Component-System related implementation details, the **metaprogramming** techniques used throughout the library will be covered in this chapter, as understanding them is a prerequisite for the analysis of ECST's modules.

## Boost.Hana

**Boost.Hana** [@boosthana] is an astonishing modern *header-only* C++14 metaprogramming library created [by Louis Dionne](http://ldionne.com/) that uses the **type-value encoding** paradigm *(a.k.a. dependent typing [@pfultz2_dependentyping])* - it is heavily used throughout ECST's implementation. By wrapping types in values, Hana allows users to perform both type-level computations and heterogeneous computations using natural syntax[^natural_hana_syntax] and with minimal compilation time overhead.

A simple example, taken from the original documentation, shows the idea behind type-value encoding:

```cpp
auto animal_types = hana::make_tuple(
    hana::type_c<Fish*>, hana::type_c<Cat&>, hana::type_c<Dog>);

auto no_pointers = hana::remove_if(animal_types, [](auto a) {
    return hana::traits::is_pointer(a);
});

static_assert(no_pointers ==
    hana::make_tuple(hana::type_c<Cat&>, hana::type_c<Dog>), "");
```

As seen in the code snippet above, types can be manipulated as values *(even using lambdas)*. Hana provides a huge number of powerful algorithms and utilities that work both on types and "traditional" values.

As an example, component and system signature lists are implemented as [`boost::hana::basic_tuple`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1basic__tuple.html) instances containing the user-specified signature types wrapped in [`boost::hana::type_c`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1type.html#ae35139e732c4b75e91061513cf445628) instances, which can be passed around like any other value and easily manipulated.



## Tags {#metaprogramming_tags}

### Motivation and usage

A very large number of methods in the library is parametrized on component types and system types. User code calling those methods would normally require the constant and inelegant use of the `instance.template method<...>(...)` template disambiguation syntax[^annoying_syntax]. **Tags** are designed to solve this problem.

Examples will be used in order to easily explain the role of tags. Here is an hypothetical set of component and system types:

```cpp
namespace c
{
    struct position { /* ... */ };
    struct velocity { /* ... */ };
    struct acceleration { /* ... */ };
}

namespace s
{
    struct velocity { /* ... */ };
    struct acceleration { /* ... */ };
}
```

Imagine a function that creates a particle using the components listed above using "traditional" template method calling syntax:

```cpp
auto make_particle = [](auto& proxy)
{
    auto eid = proxy.create_entity();

    proxy.template add_component<c::position>(eid);
    proxy.template add_component<c::velocity>(eid);
    proxy.template add_component<c::acceleration>(eid);

    return eid;
};
```

In order to prevent the mandatory `.template` disambiguation syntax and to treat component and system types as values, ECST provides **component tags** and **system tags**. **Tags** are `constexpr` wrappers that store the type information of components and systems in values, allowing them to be conveniently passed to implementation and interface functions with a natural syntax.

Tags need to be defined by the user, with the following syntax[^tag_syntax].

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

It is a good practice to separate *component types*, *system types*, *component tags* and *system tags* in separate namespaces.

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

Afterwards, calling template methods becomes much more natural:

```cpp
auto make_particle = [](auto& proxy)
{
    auto eid = proxy.create_entity();

    proxy.add_component(ct::position, eid);
    proxy.add_component(ct::velocity, eid);
    proxy.add_component(ct::acceleration, eid);

    return eid;
};
```

Manipulating and storing tags is also easier, both in user and implementation code, resulting in a more maintainable and extensible codebase.



### Implementation

All tag-related types and functions are declared in the `ecst::tag` namespace. Both component tags and system tags are implemented in the same way: a `struct` deriving from [`boost::hana::type`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1type.html) is defined, that can be immediately used in any Boost.Hana algorithm.

```cpp
namespace impl
{
    template <typename T>
    struct tag_impl : public boost::hana::type<T> { };
}
```

A `constexpr` variable called `v` *(standing for "value")* is provided as a convenient way for the user to define tags:

```cpp
template <typename T>
constexpr auto v = impl::tag_impl<T>{};
```

The types encoded inside tags can be accessed using `ecst::mp::unwrap`[^mp_namespace], which is a type alias for types stored inside [`boost::hana::type`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1type.html):

```cpp
namespace mp
{
    template <typename T>
    using unwrap = typename T::type;
}
```

Converting a traditional template method to a tag-accepting one is a straightforward process: the original method is hidden using the `private` access specifier - the new one will call it by *unwrapping* the tag:

```cpp
struct example
{
private:
    template <typename TComponent>
    auto& access_component(entity_id);

public:
    template <typename TComponentTag>
    auto& access_component(TComponentTag, entity_id eid)
    {
        return access_component<mp::unwrap<TComponentTag>>(eid);
    }
};
```

Checking if a type or a value is a tag is also possible thanks to the following utilities:

```cpp
namespace impl
{
    template <typename T>
    constexpr auto is_tag_impl =
        mp::is_specialization_of_v<tag_impl, T>;

    struct valid_t
    {
        template <typename... Ts>
        constexpr auto operator()(Ts...) const
        {
            return mp::list::all_variadic(is_tag_impl<Ts>...);
        }
    };
}

// Evaluates to true if all `xs...` are component tags.
constexpr impl::valid_t valid{};
```

Note that `valid` is implemented as a `constexpr` value *(instance of `impl::valid_t`)* and not as a regular function. This pattern is used throughout ECST, due to the fact that functions implemented as `constexpr` instances of callable objects can be easily used as arguments to other functions without the need of a lambda wrapper. This is the case for the `tag::component::is_list` and `tag::system::is_list` functions, that return whether or not the passed argument is a list of tags:

```cpp
template <typename T>
constexpr auto is_list(T x)
{
    return boost::hana::all_of(x, valid);
}
```


## Option maps {#metaprogramming_option_maps}

### Motivation and usage

User-provided compile-time settings are a vital part of ECST: in order to allow users to set options in a convenient and clear way, **option maps** were implemented using [`boost::hana::map`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1map.html) instances and method chaining. Here is an example of user code that creates a *system signature* for `s::acceleration`:

```cpp
constexpr auto ss_acceleration =
    ss::make(st::acceleration)
        .parallelism(split_evenly_per_core)
        .read(ct::acceleration)
        .write(ct::velocity);
```

The code snippet above defines `ss_acceleration` to be a system signature for `s::acceleration` with the following settings, known at **compile-time**:

* Use the `split_evenly_per_core` *inner parallelism strategy*;

* Use the `c::acceleration` component (read-only);

* Use the `c::velocity` component (mutable).

The options are provided by the user by chaining methods such as `.parallelism(...)` and `.read(...)`. The calls can be freely re-ordered, and if the same method is accidentally called twice, a compile-time error will be generated.

Defining settings using the pattern above is possible thanks to the `ecst::mp::option_map` compile-time data structure.



### Implementation

Conceptually, an option map is a compile-time associative container with the following properties:

* Keys are values fulfilling the Boost.Hana [`Comparable`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/group__group-Comparable.html) and [`Hashable`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/group__group-Hashable.html) concept;

    * A set of keys is composed by `constexpr` [`boost::hana::integral_constant`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1integral__constant.html) instances, with incrementing values.

* The keys are associated with compile-time pairs of an user-defined type and [`boost::hana::bool_c`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1integral__constant.html#aa301b96de91d665fdc846bde4659b0d3).

    * The user-defined type is option-specific;

    * The boolean integral constant is used to mark the option as *"already set"*, in order to prevent accidental multiple method calls.

Option maps are implemented as *immutable data structures*: performing operations on them returns a new option map with the desired changes.

```cpp
template <typename TMap>
class option_map
{
private:
    TMap _map;

public:
    template <typename TKey>
    constexpr auto at(const TKey& key) const;

    template <typename TKey, typename T>
    constexpr auto add(const TKey& key, T&& x) const;

    template <typename TKey, typename T>
    constexpr auto set(const TKey& key, T&& x) const;
};
```

The `_map` field is a [`boost::hana::map`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1map.html) instance. The `set` method returns a new `option_map` instance, adding `key -> (x, boost::hana::false_c)` to `_map`. The `add` method returns a new `option_map` instance, setting the value at `key` to `(x, boost::hana::true_c)` - it statically asserts the bool at `key` to be false, to prevent users from accidentally modifying a previously set option.

Using an option map to implement compile-time settings with method chaining requires the following elements:

* A class that contains an `option_map` instance and provides a clean method chaining interface;

* A set of keys representing the available options;

* An initial set of default options.

As an example, the implementation of system signatures will be analyzed.



#### Example: system signature settings

The class that contains the option map, the interface, and the system tag is declared as such:

```cpp
template <typename TTag, typename TOptionMap>
class system_signature;
```

It is default-instantiated using the `ecst::signature::system::make(...)` function:

```cpp
template <typename TSystemTag>
constexpr auto make(TSystemTag)
{
    constexpr auto default_options =
        mp::option_map::make()
            .add(keys::parallelism, ips::none::v())
            .add(keys::dependencies, hana::make_tuple())
            .add(keys::read_components, hana::make_tuple())
            .add(keys::write_components, hana::make_tuple())
            .add(keys::output, no_output);

    return system_signature<TSystemTag,
        decay_t<decltype(default_options)>>{};
}
```

The keys shown above are `constexpr` instances of Hana integral constants with unique values:

```cpp
namespace keys
{
    constexpr auto parallelism = hana::int_c<0>;
    constexpr auto dependencies = hana::int_c<1>;
    constexpr auto read_components = hana::int_c<2>;
    constexpr auto write_components = hana::int_c<3>;
    constexpr auto output = hana::int_c<4>;
}
```

After instantiating a default `system_signature` by calling `signature::system::make`, the user can modify options by using its methods, which return updated copies of the signature. After calling any number of unique methods, the final expression will evaluate to an instance of `system_signature` containing all user-desired settings.

```cpp
template <typename TTag, typename TOptionMap>
class system_signature
{
private:
    TOptionMap _option_map;

    template <typename TKey, typename T>
    constexpr auto change_self(const TKey& key, T x) const
    {
        auto new_map = _option_map.set(key, x);
        return system_signature<TTag, decay_t<decltype(new_map)>>{};
    }

public:
    template <typename TParallelismOption>
    constexpr auto parallelism(TParallelismOption x) const
    {
        return change_self(keys::parallelism, x);
    }

    // ...
};
```

Upon passing the final customized system signature to the context, ECST can retrieve the options provided by the user by querying `_option_map`. This pattern is currently used to implement **system signatures**, **component signatures** and **context settings**.



## Other techniques and algorithms

A number of other metaprogramming techniques and compile-time algorithms are used throughout ECST:

* A **breadth-first traversal** algorithm is used to find and count dependencies in isolated system chains - it is covered in [Chapter 14, Section 14.4](#appendix_compiletime_bfs);

* Compile-time **tuple element iteration** is used to build *component type bitsets*, to start parallel system execution and to run tests with various combinations of settings. See [Chapter 14, Section 14.2](#appendix_component_bitset_creation) for more details;

* **SFINAE**, `std::enable_if_t`, and generic lambdas with trailing return types are used together with [`boost::hana::overload`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/overload_8hpp.html) to implement *system execution adapters*, *refresh event handling*, and *generic system execution*. These techniques will be covered in [Chapter 8](#chap_flow) and [Chapter 12](#chap_advfeats).



[^natural_hana_syntax]: syntax that "looks like" regular run-time computation syntax.

[^tag_syntax]: preprocessor macros can be used to reduce required boilerplate code.

[^mp_namespace]: the `ecst::mp` namespace contains metaprogramming-related utilities.

[^annoying_syntax]: such syntax negatively impacts the readability of the code and is essentially avoidable boilerplate. It is required due to ambiguous parsing for the `<` token, which could be interpreted both as an *"angle bracket"* or as a *less-than operator*. Details can be found [on cppreference](http://en.cppreference.com/w/cpp/language/dependent_name#The_template_disambiguator_for_dependent_names).