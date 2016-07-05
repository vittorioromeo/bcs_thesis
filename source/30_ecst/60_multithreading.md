


# Multithreading

Multithreading is used in ECST in the following situations, to potentially increase the run-time performance of user applications:

* **Outer parallelism**: system chains independent from each other can run in parallel. Implemented with **system scheduling**;

* **Inner parallelism**: system execution can be split over multiple *subtasks*. Implemented with **inner parallelism strategies** and **slicing**;

* **Refresh**: some operations in the [refresh stage](#flow_refresh) can run in parallel.



## Thread pool
Execution of operations in separate threads is achieved through a simple **thread pool** which consists of a **lock-free queue** and a number of **workers**. Every worker runs on a separate thread and continuously dequeues **tasks** from the queue, executing them.

\dot(source/figures/generated/ecst/multithreading/threadpool { width=75% })
(ECST multithreading: thread-pool architecture)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir = LR

    subgraph cluster_workers
    {
        label = "Workers"
        C[shape = "record", rank = -10000, label = "<f0> W0 | <f1> W1 | <f2> W2"]
        C
    }

    subgraph cluster_queue
    {
        label = "Task queue"
        Queue[shape = "record", rank = 10000, label = "{<fx> ... | T3 | T2 | T1 | <f0> T0}"]
        Queue
    }

    Queue:f0 -> C:f0
    Queue:f0 -> C:f1
    Queue:f0 -> C:f2

    Context->Queue : fx
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Tasks are implemented using `ecst::fixed_function`, similar to `std::function` but with a fixed allocation size. Synchronization is implemented using `std::condition_variable` and `std::atomic` counters. An implementation making use of `std::packaged_task` and `std::future` was tested, but the unnecessary overhead brought by those classes was significant.



### Lock-free queue
To provide **workers** with tasks, a third-party blocking concurrent lock-free queue developed by Cameron Desrochers is used. The queue class is called `moodycamel::BlockingConcurrentQueue`, and is [available on GitHub](https://github.com/cameron314/concurrentqueue) under the *Simplified BSD License*.

The queue is used in the worker code as follows:

```cpp
void worker::run()
{
    task t;

    while(_state == state::running)
    {
        _queue->wait_dequeue(t);
        t();
    }
}
```

The `_queue->wait_dequeue(t)` method call will block the current thread until the queue is not empty, and then dequeue a task into `t`. In order to prevent indefinitely waiting upon thread pool destruction, a number of *"dummy"* empty tasks are spawned to wake up the waiting workers:

```cpp
thread_pool::~thread_pool()
{
    // Signal all workers to exit their processing loops.
    for(auto& w : _workers) w.stop();

    // Post dummy tasks until all workers have exited their loops.
    while(!all_workers_finished()) post_dummy_task();

    // Join the workers' threads.
    for(auto& w : _workers) w.join();
}
```



## Synchronization

Synchronization and waiting are required when implementing both outer and inner parallelism:

* When executing outer parallelism, systems must wait for **all** their dependencies to complete before starting execution.

* When executing inner parallelism, **all** subtasks must be finished in order to complete a system execution.

The waiting conditions are very simple and can easily and efficiently be implemented using `std::condition_variable` and `std::atomic` counters. ECST provides a convenient and safe waiting interface, obtained by  wrapping the aforementioned synchronization primitives alongside an `std::mutex` in a data structure called `counter_blocker`:

```cpp
struct counter_blocker
{
    std::condition_variable _cv;
    std::mutex _mutex;
    std::atomic<std::size_t> _counter;

    counter_blocker(std::size_t initial_count)
        : _counter{initial_count}
    {
    }
};
```

The `counter_blocker` can be used as follows:

```cpp
// Create a `counter_blocker` initialized to `n`.
counter_blocker cb{n};

// Immediately execute the passed function and block
// until `cb` reaches zero.
execute_and_wait_until_counter_zero(cb, [&]
    {
        // `spawn_tasks` needs to decrement the counter.
        spawn_tasks(cb, n);
    });
```

Here's a possible implementation for `spawn_tasks`:

```cpp
void spawn_tasks(counter_blocker& cb, int n)
{
    for(int i = 0; i < n; ++i)
    {
        post_in_thread_pool([&]
            {
                // Decrement the counter inside `cb` and
                // notify one thread.
                decrement_cv_counter_and_notify_one(cb);
            });
    }
}
```

The pattern shown above is used in the implementation of both outer and inner parallelism and in the refresh stage.

### Implementation details

The synchronization operations are hidden behind an interface that takes a reference to a `counter_blocker`:

```cpp
void decrement_cv_counter_and_notify_one(counter_blocker&);
void decrement_cv_counter_and_notify_all(counter_blocker&);

template <typename TF>
void execute_and_wait_until_counter_zero(counter_blocker&, TF&&);
```

The functions above call implementation functions by explicitly passing `counter_blocker` members. The most primitive implementation function is `access_cv_counter`, which calls a passed function after safely accessing the counter inside a `counter_blocker`:

```cpp
template <typename TF>
void access_cv_counter(
    mutex_type& m, cv_type& cv, counter_type& c, TF&& f)
{
    lock_guard_type l(m);
    f(cv, c);
}
```

It is used as a building block for the *"decrement and notify"* functions:

```cpp
void decrement_cv_counter_and_notify_one(
    mutex_type& m, cv_type& cv, counter_type& c)
{
    access_cv_counter(m, cv, c, [](auto& x_cv, auto& x_c)
        {
            assert(x_c > 0);
            --x_c;
            x_cv.notify_one();
        });
}
```

The *"execute and wait"* functions are implemented using an `std::unique_lock` waiting on a generic predicate through the `std::condition_variable` stored in the `counter_blocker`:

```cpp
template <typename TPredicate, typename TF>
void execute_and_wait_until(
    mutex_type& m, cv_type& cv, TPredicate&& p, TF&& f)
{
    unique_lock_type l(m);
    f();
    cv.wait(l, p);
}

template <typename TF>
void execute_and_wait_until_counter_zero(
    mutex_type& m, cv_type& cv, counter_type& c, TF&& f)
{
    execute_and_wait_until(m, cv,
        [&c]
        {
            return c == 0;
        },
        f);
}
```


## System scheduling

**System scheduling** implements the concept of *outer parallelism*. The user can begin system execution during a [*step stage*](#step_stage) from any number of independent systems:

```cpp
ctx.step([&](auto& proxy)
{
    // Start execution of system chains from `s::s0` and `s::s1`:
    proxy.execute_systems_from(st::s0, st::s1)(
        sea::t(st::s0).for_subtasks([dt](auto& s, auto& data)
            {
                // Overload for `s::s0`.
                s.process(dt, data);
            }),
        sea::t(st::s1).for_subtasks([dt](auto& s, auto& data)
            {
                // Overload for `s::s1`.
                s.process(dt, data);
            }));
});
```

The `s::s0` and `s::s1` system types need to be independent of each other *(a compile-time error will occur otherwise)*. After calling `proxy.execute_systems_from`, the [system manager](#architecture_system_mgr) inside the context will instantiate a system scheduler and begin execution:

```cpp
template <typename TSettings>
template <typename TCtx, typename TSystemTagList, typename... TFs>
void system_manager<TSettings>::execute_systems_impl(
    TCtx& ctx, TSystemTagList sstl, TFs&&... fs)
{
    // Instantiate system scheduler (specified in context settings).
    scheduler_type s;

    // Overload user-provided functions.
    auto o_fs = boost::hana::overload_linearly(fs...);

    // Begin execution.
    // (Blocks until all systems in the chain have been executed.)
    s.execute(ctx, sstl, os);
}
```

The current only default system scheduler type is called `atomic_counter` - it `counter_blocker` instances to wait for system dependencies' execution completion.

### Atomic counter scheduler {#mt_ac_scheduler}

The `atomic_counter` scheduler keeps count of the remaining systems *(yet to be executed)* and assigns a **task** to every system. Every task keeps count of its **remaining dependencies**. Tasks are executed recursively - after completing the starting independent tasks, every **dependent task** *(child task)* whose dependencies were satisfied is executed.

The scheduler will block until all systems have been executed, and all dependencies between systems will be respected. Here's a high-level pseudocode of the algorithm:

\begin{algorithm}[H]

\caption{ECST multithreading: system scheduler - atomic counter}
\footnotesize

\SetKwFunction{GetChainSize}{GetChainSize}
\SetKwData{StartTags}{startSystems}
\SetKwData{CurrentSystems}{currentSystems}
\SetKwData{RemainingSystems}{remainingSystems}

\SetKwFunction{ExecuteSystems}{ExecuteSystems}
\SetKwFunction{RunChain}{RunTask}
\SetKwFunction{TaskFromSystem}{TaskFromSystem}
\SetKwFunction{SystemOf}{SystemOf}
\SetKwFunction{DependentTasks}{DependentTasks}
\SetKwFunction{DecrementAtomicCounter}{DecrementAtomicCounter}

\SetKwFunction{DecrementRemainingDependencies}{DecrementRemainingDependencies}
\SetKwFunction{RemainingDependenciesCount}{RemainingDependenciesCount}

\SetKwInOut{Input}{input}\SetKwInOut{Output}{output}

\SetKwBlock{BlockWhile}{}{end}
\SetKw{BlockWhileKw}{block thread while}
\SetKw{KwEnd}{end}

\SetKwData{T}{t}
\SetKwData{Dt}{dt}
\SetKwData{S}{s}
\SetKwData{F}{f}


\Input{List of starting system tags \StartTags}
\Input{Overloaded processing function \F}

\SetKwFunction{algo}{algo}\SetKwFunction{proc}{proc}
\SetKwProg{myalg}{Algorithm}{}{}

\SetAlgoLined

    \BlankLine

    \myalg{\ExecuteSystems{\StartTags, \F}}{
        \tcc{count unique nodes traversed from every starting system}
        \RemainingSystems $\longleftarrow$ \GetChainSize{\StartTags}\;

        \BlankLine

        \tcc{start recursive task execution}
        \ForEach(in parallel){system \S $\in$ \StartTags}{
            \T $\longleftarrow$ \TaskFromSystem{\S}\;
            \RunChain{\RemainingSystems, \T, \F}\;
        }

        \BlankLine

        \tcc{block until all systems have been executed}
        \BlockWhileKw \RemainingSystems $> 0$\;
    }
    \KwEnd

    \BlankLine
    \BlankLine

    \SetKwProg{myproc}{Procedure}{}{}
    \myproc{\RunChain{\RemainingSystems, \T, \F}}{

        \tcc{execute current task}
        \F{\SystemOf{\T}}\;
        \DecrementAtomicCounter{\RemainingSystems}\;
        \BlankLine


        \tcc{for each dependent child task}
        \ForEach{task \Dt $\in$ \DependentTasks{\T}}{

            \tcc{notify \Dt the current (parent) task was executed}
            \DecrementRemainingDependencies{\Dt}\;

            \BlankLine

            \tcc{run \Dt recursively if its dependencies were satisfied}

            \If{\RemainingDependenciesCount{\Dt} $ == 0$}{
                \RunChain{\RemainingSystems, \Dt, \F}\;
            }
        }
    }
    \KwEnd

\end{algorithm}

The implementation of the algorithm above will be now analyzed in the sections below.







#### Starting chain execution {#mt_s_sce}

The first step is traversing the implicit dependency **directed acyclic graph**, from every user-provided starting system type, counting the unique traversed nodes. This is done with a compile-time [**breadth-first traversal**](#appendix_compiletime_bfs).

```cpp
template <typename TCtx, typename TSystemTagList, typename TF>
void atomic_counter::execute(TCtx& ctx, TSystemTagList sstl, TF&& f)
{
    // Count of nodes traversed starting from every node in `sstl`.
    constexpr auto n = signature_list::system::chain_size(ssl, sstl);

    // Counter blocker used to block until all systems in the chain
    // have been executed.
    counter_blocker b{n};

    // Begin the execution and block until all systems have finished.
    execute_and_wait_until_counter_zero(b, [&]() mutable
        {
            this->start_execution(ctx, sstl, b, f);
        });
}
```

`atomic_counter::start_execution` will begin the recursive task execution.



#### Recursive task execution {#multithreading_recursive_task_execution}

Every system in the context has an assigned task, which has a unique ID. `atomic_counter::start_execution` retrieves the tasks of the starting systems and executes them recursively:

```cpp
template <typename TCtx, typename TSystemTagList, typename TBlocker,
    typename TF>
void atomic_counter::start_execution(
    TCtx& ctx, TSystemTagList sstl, TBlocker& b, TF&& f)
{
    // For each system tag in `sstl`...
    boost::hana::for_each(sstl, [&](auto st) mutable
        {
            // Get the corresponding task ID.
            auto sid = sls::id_by_tag(this->ssl(), st);

            // Run task with ID `sid`.
            ctx.post_in_thread_pool([&]() mutable
                {
                    this->task_by_id(sid).run(b, id, sp, f);
                });
        });
}
```

After retrieving a task by ID, `atomic_counter::task::run` will effectively execute the overloaded user-provided processing function on the system and recursively run children tasks with no remaining dependencies:

```cpp
template <typename TBlocker, typename TID, typename TCtx, typename TF>
void atomic_counter::task::run(TBlocker& b, TID sid, TCtx& ctx, TF&& f)
{
    // Get reference to system instance from task ID.
    auto& s_instance(ctx.instance_by_id(sid));

    // Execute overloaded processing function on system instance.
    s_instance.execute(ctx, f);

    // Safely decrement "remaining systems" counter.
    decrement_cv_counter_and_notify_one(b);

    // For every dependent task ID...
    for_dependent_ids([&](auto id)
        {
            // Retrieve the corresponding task.
            auto& dt = task_by_id(id);

            // Then, inform the task that one of its dependencies (the
            // current task) has been executed.
            dt.decrement_remaining_dependencies();

            if(dt.remaining_dependencies() == 0)
            {
                // Recursively run the dependent task.
                ctx.post_in_thread_pool([&]
                    {
                        dt.run(b, id, ctx, f);
                    });
            }
        });
}
```

## Inner parallelism {#multithreading_inner_par}

**Inner parallelism** allows single systems to be run in parallel by *splitting* the range of their subscribed entities across a number of **subtasks**. Every subtask has its own **state** and can run in a separate thread. **Parallel executors**, which are obtained by composing **inner parallelism strategies**, implement the concept of *inner parallelism*.



### Parallel executor {#multithreading_par_executor}
Every *system instance* stores a **parallel executor**. Parallel executors wrap inner parallelism strategies composed at compile-time by library users. Here is an example definition of an inner parallelism strategy:

```cpp
namespace ips = ecst::inner_parallelism::strategy;
namespace ipc = ecst::inner_parallelism::composer;

constexpr auto my_parallelism_strategy =
    ipc::none_below_threshold::v(sz_v<10000>,
        ips::split_evenly_fn::v_cores()
        );

constexpr auto ss_acceleration =
    ss::make(st::acceleration)
        .parallelism(my_parallelism_strategy)
        .read(ct::acceleration)
        .write(ct::velocity);
```

The code snippet above configures `s::acceleration` to run in a single thread if its subscriber count is less than $10000$, otherwise it will be evenly split across the available CPU cores.

System instances invoke the parallel executor by passing a reference to the parent context, a **subtask adapter** function, and the overloaded user-provided processing function. The subtask adapter binds a `counter_blocker`, the context and the processing function to a new function which will *slice* the subscribed entity range depending on parameters provided by the inner parallelism strategy:

```cpp
template <typename TContext, typename TF>
void instance</* ... */>::execute_in_parallel(TContext& ctx, TF&& f)
{
    auto subtask_adapter = [this](auto& b, auto& x_ctx, auto&& xf)
    {
        return [&](auto split_idx, auto i_begin, auto i_end)
        {
            // Nullary function that will process the entities in
            // the `[i_begin, i_end)` range.
            auto bse = this->make_bound_slice_executor(
                b, x_ctx, split_idx, i_begin, i_end, xf);

            this->run_subtask_in_thread_pool(x_ctx, std::move(bse));
        };
    };

    _parallel_executor.execute(
        *this, ctx, std::move(subtask_adapter), f);
}
```

This design has been chosen in order to easily implement other system instance types in the future *(e.g. systems that directly process component data, without knowledge of entities)*. The parallel executor implementation will ask the caller instance to prepare execution of $n$ subtasks:

```cpp
template <typename TInstance, typename TCtx, typename TFAdapter,
    typename TF>
void split_every_n</* ... */>::execute(
    TInstance& i, TCtx& ctx, TFAdapter&& fa, TF&& f)
{
    // Perform strategy-related calculations.
    auto per_split = /* ... */;
    auto split_count = /* ... */;

    // Prepare and execute `split_count` subtasks and block until
    // their execution is complete.
    i.prepare_and_wait_n_subtasks(split_count, [&](auto& b)
        {
            auto adapted_subtask(fa(b, ctx, f));

            // Builds and runs the subtasks.
            utils::execute_split(
                i.subscribed_count(), per_split, split_count,
                adapted_subtask);
        });
}
```

The `instance::prepare_and_wait_n_subtasks` method takes care of initializing the `counter_blocker` with the number of produced subtasks and of starting the subtask execution:

```cpp
template <typename TF>
void instance</* ... */>::prepare_and_wait_n_subtasks(int n, TF&& f)
{
    // Clear and prepare substask states.
    _sm.clear_and_prepare(n);

    // Initialize a `counter_blocker`.
    counter_blocker b{n};

    // Runs the subtasks and blocks until the counter reaches zero.
    execute_and_wait_until_counter_zero(b, [&]{ f(b); });
}
```


#### Slicing {#inner_par_slicing}

The implementation of `make_bound_slice_executor` creates a *nullary[^nullary] function* that can be executed in a separate thread by binding all required parameters. The function instantiates a **data proxy** that is used in the system implementation code. The data proxy uses the bound parameters to provide a slice of subscribed entities behind a uniform interface *([syntax-level transparency](#ecstoverview_syntaxtransp))*.

```cpp
template <typename TSettings, typename TSystemSignature>
template <typename TBlocker, typename TCtx>
auto instance<TSettings, TSystemSignature>::make_slice_executor(
    TBlocker& b, TCtx& ctx,
    int state_idx, int i_begin, int i_end, TF&& f)
{
    // The returned function will be executed by a thread pool worker.
    return [&, state_idx, i_begin, i_end]
    {
        // Create a "data proxy".
        auto dp = data_proxy::make<TSystemSignature>(/* ... */);

        // Execute the user-defined processing function, passing the
        // proxy as an argument.
        f(dp);

        // Decrement counter and notify waiting threads.
        decrement_cv_counter_and_notify_all(b);
    };
}
```



[^nullary]: that takes no arguments.