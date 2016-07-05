



# Miscellaneous



## Sparse integer sets {#appendix_sparse_integer_sets}

A **sparse integer set** is a data structures representing a set of positive integers with the following time complexity characteristics:

|                           | Time complexity  |
|---------------------------|:----------------:|
| Check presence of integer | $\mathcal{O}(1)$ |
| Add integer to set        | $\mathcal{O}(1)$ |
| Remove integer from set   | $\mathcal{O}(1)$ |
| Iterate over integers     | $\mathcal{O}(n)$ |

Its space complexity is $\mathcal{O}(n)$.

Sparse integers sets are perfect for entity ID management, as the complexity of all required operations is optimal. They have been extensively covered in [@sparsesets132] and [@sparsesets_praxis]. A possible C++ implementation is analyzed in [@sparsesets_cpp]. Sparse integer sets have been already used in existing ECS libraries: an example is *Diana*, by Vincent Adam Burns [@github_diana].



### Implementation details

Sparse integer sets are implemented in **vrm_core** *(see [@github_vrmcore])*, which is a dependency of ECST. The used storage types depend on context settings *([static dispatching](#appendix_static_dispatching))*, but conceptually every implementation is composed of the following elements:

* An unordered **dense array** $D$, which contiguously stores all integers present in the set;

* A **sparse array** $S$, containing indices to the elements of $D$, or special null $\emptyset$ values.

![ECST miscellaneous: fixed sparse integer set example](source/figures/sparseset.png){#sparsesetexample width=85% }

#### Operation: contains

Checking whether or not an integer $i$ is in the set consists in checking if $S_i \neq \emptyset$.



#### Operation: iteration

Iterating over the integers in the set consists in iterating over $D$.



#### Operation: add integer to set

Adding an integer $i$ to the set consists in appending it to $D$ and making $S_i$ *point* to $D_{last}$.

\begin{algorithm}[H]

\caption{ECST miscellaneous: SparseIntSet - AddInteger}
\footnotesize

\SetKwData{I}{i}
\SetKwArray{D}{D}
\SetKwArray{S}{S}
\SetKwData{Last}{last}
\SetKwFunction{Contains}{Contains}

    \tcc{do nothing if \I is already in the set}
    \If{\Contains{\I} $=$ false}{
        \tcc{append \I to \D}
        \D{\Last} $\longleftarrow$ \I\;

        \tcc{make \S{\I} "point" to \I}
        \S{\I} $\longleftarrow$ \Last;
    }

\end{algorithm}



#### Operation: remove integer from set

Removing an integer $i$ from the set consists in swapping $i$ with $D_{last}$ if necessary, then updating $S_i$ and decrementing the number of contained integers.

\begin{algorithm}[H]

\caption{ECST miscellaneous: SparseIntSet - RemoveInteger}
\footnotesize

\SetKwData{I}{i}
\SetKwData{J}{iPtr}
\SetKwArray{D}{D}
\SetKwArray{S}{S}
\SetKwData{Last}{last}
\SetKwFunction{Contains}{Contains}

    \tcc{do nothing if \I is not in the set}
    \If{\Contains{\I} $=$ true}{
        \tcc{access \S{\I}}
        \J $\longleftarrow$ \S{\I}\;

        \tcc{check if \J is the last element in \D}
        \If{\D{\Last} $\neq$ \D{\J}}{
            \tcc{if not, swap \J with the last element and update \S}
            \D{\J} $\longleftarrow$ \D{\Last}\;
            \S{\Last} $\longleftarrow$ \J\;
        }

        \tcc{nullify \S{\I} and decrement \Last}
        \S{\I} $\longleftarrow \emptyset$\;
        ${-}{-}$\Last\;
    }

\end{algorithm}



## Component bitset creation {#appendix_component_bitset_creation}

**Component bitsets** are *dense bitsets* implemented with `std::bitset` used to keep track of an entity's components and to efficiently check whether or not an entity belongs to a system. Every component type is represented by a unique bit.

[System instances](#storage_system) store a component bitset that represents the required component types for subscription. The bitset is generated from a [system signature](#system_sigs), using compile-time tuple iteration and Boost.Hana algorithms.

Firstly, the component types specified in the system signature are retrieved and concatenated:

```cpp
template <typename TSettings, typename TSystemSignature>
auto make_from_system_signature(TSettings s, TSystemSignature ss)
{
    // Tag list of components read by `ss`.
    auto read_ctag_list = signature::system::read_ctag_list(ss);

    // Tag list of components written by `ss`.
    auto write_ctag_list = signature::system::write_ctag_list(ss);

    // Concatenate the two lists.
    auto ctag_list =
        boost::hana::concat(read_ctag_list, write_ctag_list);

    return make_from_tag_list(s, ctag_list);
}
```

Tags are values, and that type lists are `boost::hana::tuple` instances. Boost.Hana provides a `boost::hana::for_each` function that can be used to *"iterate"* over the elements of a tuple at compile-time. Building the bitset simply consists in iterating over `ctag_list` and setting the corresponding component bits to `1`:

```cpp
template <typename TSettings, typename TComponentTagList>
auto make_from_tag_list(TSettings s, TComponentTagList ctl)
{
    // Create empty `std::bitset` with length equal to the
    // number of components.
    component_bitset<TSettings> b;

    // Retrieve the complete list of component signatures
    // from the context settings.
    auto csl = settings::component_signature_list(s);

    // For each tag in `ctl`...
    boost::hana::for_each(ctl, [&](auto ct)
        {
            // Retrieve the unique component ID from `csl`.
            auto id(signature_list::component::id_by_tag(csl, ct));

            // Set the corresponding bit.
            b.set(id, true);
        });

    return b;
}
```



## Static dispatching {#appendix_static_dispatching}

**"Static dispatching"** is the term used in ECST to refer to compile-time choices regarding data structures. It is used to avoid unnecessary overhead depending on user-specified context settings. An example use case can be found in the implementation of [entity metadata storage](#storage_entity): `std::array` or `std::vector` will be used to store metadata depending on the *fixed*/*dynamic* entity limit choice made by the user.

### Implementation details

Most occurrences of static dispatching are implemented using `static_if`, available in **vrm_core** *(see [@github_vrmcore])*. A compile-time branching construct is not yet part of the standard, but it has been proposed several times *(see [@isocpp_sif0], [@isocpp_sif1], [@isocpp_sif2] and [@isocpp_sif3])* and it's likely to be introduced in C++17. Nevertheless, a `static_if` construct that's more convienient and localized than *explicit template specialization* [@cppreference_ets] can be implemented using C++14 features *(see [@sif0], [@sif1] and [@sif2])*.

Using `static_if`, implementing static dispatching becomes straightforward. An auxiliary `dispatch_on_storage_type` function executes one of the passed callable objects depending on the user-specified storage limitations:

```cpp
template <typename TSettings, typename TFFixed, typename TFDynamic>
auto dispatch_on_storage_type(
    TSettings&& s, TFFixed&& f_fixed, TFDynamic&& f_dynamic)
{
    return static_if(s.has_fixed_capacity())
        .then([&](auto xs)
            {
                return f_fixed(xs.get_fixed_capacity());
            })
        .else_([&](auto xs)
            {
                return f_dynamic(xs.get_dynamic_capacity());
            })(s);
}
```

Using the function above, data structures wrapped in [`boost::hana::type_c`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1type.html#ae35139e732c4b75e91061513cf445628) can be returned and later instantiated. Here is the implementation of the function statically dispatching entity metadata storage types:

```cpp
template <typename TSettings>
auto dispatch_entity_storage(TSettings s)
{
    return settings::dispatch_on_storage_type(s,
        [](auto fixed_capacity)
        {
            return boost::hana::type_c<
                impl::fixed_entity_storage<
                    metadata_type<TSettings>,
                    fixed_capacity>
                >;
        },
        [](auto)
        {
            return boost::hana::type_c<
                impl::dynamic_entity_storage<
                    TSettings,
                    metadata_type<TSettings>>
                >;
        });
}
```



## Compile-time breadth-first traversal {#appendix_compiletime_bfs}

A compile-time version of the **breadth-first traversal** algorithm was implemented in order to allow users to begin system execution from particular independent nodes. A complete [system signature list](#ctopts_siglist) represents a DAG that can be composed of multiple *connected components* - knowledge of the exact number of nodes in a connected component is required to properly execute the system chain using the ["atomic counter" scheduler](#mt_ac_scheduler).

Graph traversal algorithms provide a straightforward way of counting the number of unique nodes in a connected component. The BFT algorithm was chosen for this task: in short, it traverses a graph starting from a particular node and exploring all neighbor nodes first. Explored nodes have to be *"marked"* to prevent redundant traversals.

Breadth-first traversal is easy to implement using mutable data structures:

* A queue is used to keep track of the nodes that need to be explored;

    * Unmarked neighbors of the node currently being explored are enqueued for future traversal.

* Explored nodes need to be marked as *"visited"* to guarantee each node being traversed exactly once.

Similarly to the implementation of [option maps](#metaprogramming_option_maps), the required state is implemented using immutable Boost.Hana data structures whose operations yield a new *(copy)* updated structure instead of mutating the structure in-place.

* Nodes are compile-time numerical IDs *([`boost::hana::integral_constant`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1integral__constant.html));

* The BFT queue is a [`boost::hana::tuple`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1tuple.html);

* Nodes are *"marked as visited"* by storing their ID in a [`boost::hana::tuple`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1tuple.html);

* Both the queue and the *"visited nodes tuple"* are stored in a [`boost::hana::pair`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/structboost_1_1hana_1_1pair.html). The pair is referred to as the **BFT context**.

All operations are defined inside the `bf_traversal` namespace. The data structures can be initialized and accessed with the following functions:

```cpp
namespace bf_traversal
{
    template <typename TStartNodeList>
    constexpr auto make(TStartNodeList&& snl)
    {
        return hana::make_pair(snl, hana::make_tuple());
    }

    template <typename TBFTContext>
    constexpr auto queue(TBFTContext&& c)
    {
        return hana::first(c);
    }

    template <typename TBFTContext>
    constexpr auto visited(TBFTContext&& c)
    {
        return hana::second(c);
    }
}
```

Convenient functions to query the state of the BFT context are defined as well:

```cpp
namespace bf_traversal
{
    template <typename TBFTContext, typename TNode>
    constexpr auto is_visited(TBFTContext&& c, TNode&& n)
    {
        return hana::contains(visited(c), n);
    }

    template <typename TBFTContext, typename TNode>
    constexpr auto is_in_queue(TBFTContext&& c, TNode&& n)
    {
        return hana::contains(queue(c), n);
    }

    template <typename TBFTContext>
    constexpr auto is_queue_empty(TBFTContext&& c)
    {
        return hana::is_empty(queue(c));
    }

    template <typename TBFTContext>
    constexpr auto top_node(TBFTContext&& c)
    {
        return hana::front(queue(c));
    }
}
```

The algorithm is executed through the `bf_traversal::execute` function, which takes a list of starting nodes and the complete system signature list as parameters. A `step` lambda, which repeatedly yields updated BFT context instances, is executed recursively until the traversal is completed by using [`boost::hana::fix`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/group__group-functional.html#ga1393f40da2e8da6e0c12fce953e56a6c), which is an implementation of the **"Y-combinator"** *(a.k.a. "fixed-point combinator")*. `bf_traversal::execute` returns a list of the traversed node IDs.

```cpp
template <typename TStartNodeList, typename TSSL>
auto execute(TStartNodeList&& snl, TSSL ssl)
{
    // Recursive step.
    // Takes itself as `self`, and the current context.
    auto step = [=](auto self, auto&& ctx)
    {
        return static_if(bf_traversal::is_queue_empty(ctx))
            .then([=](auto)
                {
                    // Base case: empty BFT queue.
                    // Return an empty tuple.
                    return hana::make_tuple();
                })
            .else_([=](auto&& x_ctx)
                {
                    // Recursive case.
                    // Call `self` with the updated context
                    // returned by `step_forward`.
                    // Append the last visited node to the
                    // final result.

                    auto updated_ctx =
                        step_forward(x_ctx, ssl);

                    return hana::append(
                        self(updated_ctx),
                        top_node(x_ctx));
                })(ctx);
    };

    // Begin the recursion vy initializing a BFT context.
    return hana::fix(step)(make(snl));
}
```

The core of the algorithm resides in the `bf_traversal::step_forward` function:

```cpp
template <typename TBFTContext, typename TSSL>
auto step_forward(TBFTContext&& c, TSSL ssl) noexcept
{
    // Dequeue the first node.
    auto pop_queue = hana::remove_at(queue(c), mp::sz_v<0>);

    // List of neighbors of the dequeued node.
    auto neighbors = dependent_ids_list(
        ssl, signature_by_id(ssl, top_node(c)));

    // Filter out already visited neighbors.
    auto unvisited_neighbors =
        hana::remove_if(neighbors, [=](auto x_nbr)
            {
                return is_visited(c, x_nbr);
            });

    // Updated queue.
    auto new_queue =
        hana::concat(pop_queue, unvisited_neighbors);

    // Updated "visited nodes" list.
    auto new_visited =
        hana::concat(visited(c), unvisited_neighbors);

    // Updated BFT context.
    return hana::make_pair(new_queue, new_visited);
}
```

The last missing piece is the implementation of `dependent_ids_list`, which returns a list of nodes that depend on the passed *"parent node"*. It is implemented by iterating over the complete system signature list *(using [`boost::hana::fold_right`](http://www.boost.org/doc/libs/1_61_0/libs/hana/doc/html/fold__right_8hpp.html))*, gathering all nodes that have the *"parent node"* as one of their dependencies:

```cpp
template <typename TSystemSignatureList, typename TSystemSignature>
auto dependent_ids_list(
    TSystemSignatureList ssl, TSystemSignature parent)
{
    namespace ss = signature::system;
    namespace sls = signature_list::system;

    // Retrieve the id of `parent`.
    auto parent_id = sls::id_by_signature(ssl, parent);

    // Build a list of dependent IDs.
    return hana::fold_right(ssl, hana::make_tuple(),
        [=](auto ss, auto acc)
        {
            // Check if `parent_id` is one of `ss`'s depedendencies.
            auto dl = sls::dependencies_as_id_list(ssl, ss);
            return static_if(hana::contains(dl, parent_id))
                .then([=](auto x_acc)
                    {
                        // If so, add `ss`'s ID to the result list.
                        auto ss_id = sls::id_by_signature(ssl, ss);
                        return hana::append(x_acc, ss_id);
                    })
                .else_([=](auto x_acc)
                    {
                        return x_acc;
                    })(acc);
        });
}
```

[The algorithm is used in the implementation of the `atomic_counter::execute` scheduler function](#mt_s_sce), under the name `chain_size`, in order to instantiate a `counter_blocker` that will block the calling thread until all systems belonging to a particular connected component of the dependency DAG have been executed.