


# Execution flow {#chap_flow}

Using ECST requires the user to follow a particular **execution flow**, composed of different stages. The execution flow restricts possible operations *(using [proxy objects](#chap_proxies))* in order to keep the state of the application consistent and to avoid a set of race conditions.

Before examining the execution flow, **critical operations** will be defined in the following section.

## Critical operations

Some of the actions that can be executed in specific stages of the execution flow are called **critical operations**. These operations may require **memory allocations** and/or **synchronization** - they have to be executed sequentially. Execution of critical operations can happen immediately in some contexts *(e.g. during a **step**)* or can be delayed using **deferred functions** in other contexts *(e.g. system execution)*.

Critical operations include:

* Creating or destroying an entity;

* Adding or removing a component to/from an entity;

* Starting the execution of a system chain.

Non-critical operations include:

* Using a system's output data;

* Marking an entity as *"dead"*;

* Accessing or mutating existing component data.

An example containing critical and non-critical operations in a system implementation is shown below:

```cpp
template <typename TData>
void process_collision_particles(TData& data)
{
    data.for_entities([&](auto eid)
        {
            // Reading/mutating components is a
            // non-critical operation.
            const auto& contact_list =
                data.get(ct::contact, eid);

            for(const auto& c : contact_list)
            {
                // Critical operation can be delayed
                // to a later stage.
                data.defer([&](auto& proxy)
                    {
                        // Creating entities and adding
                        // or removing components is a
                        // critical operation.
                        auto p = proxy.create_entity();
                        proxy.add_component(ct::particle, p);
                    });
            }

            if(!contact_list.empty())
            {
                // Marking an entity as "dead" is a
                // non-critical operation.
                data.kill_entity(eid);
            }
        });
}
```

## Flow stages

ECST's execution flow is composed of the following stages: **step**, **system execution**, **refresh**.

### Step {#step_stage}

**Step** stages are accessed through a `context`, using a **step proxy**.

They:

* Allow immediate execution of *non-critical operations*;

* Allow immediate execution of *critical operations*;

* Allow execution of system chains;

* Execute a **refresh** after completion.

\dot(source/figures/generated/ecst/flow/stepact { width=90% })
(ECST flow: "step" stage overview)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    Done [label="Done?", shape="diamond"]

    subgraph cluster_step
    {
        label="Step stage"

        Choice [label="", shape="diamond", width=".2", height=".2", fixedsize="true"]

        NonCrit [label="Non-critical operation", shape="rectangle"]

        Crit [label="Critical operation", shape="rectangle"]

        Chain [label="System chain", shape="rectangle"]

        ChoiceEnd [label="", shape="diamond", width=".2", height=".2", fixedsize="true"]
    }

    Start [label="", shape="point", width="0.25", height="0.25", fixedsize="true"]

    Start -> Choice

    Done -> Choice  [label=" no"]

    Choice -> NonCrit
    Choice -> Crit
    Choice -> Chain

    NonCrit -> ChoiceEnd
    Crit -> ChoiceEnd
    Chain -> ChoiceEnd

    ChoiceEnd -> Done

    Done -> Chain [style=invis]

    Done -> Refresh [label=" yes"]

    End [label="", shape="doublecircle", width="0.25", height="0.25", fixedsize="true", fillcolor="black", style=filled]

    Refresh -> End
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#### User code

A step can be defined in user code by calling `context::step(...)` with a function that accepts a *step proxy*. The following example shows a code snippet in which the user, inside of a step stage, prepares a rendering system, executes a system chain that processes physics and generates vertices, and finally renders the generated vertices to the window.

```cpp
namespace sea = ::ecst::system_execution_adapter;

context.step([&](auto& proxy)
{
    proxy.system(st::render).prepare();

    proxy.execute_systems(
        sea::t(st::physics).for_subtasks(
            [dt](auto& s, auto& data)
            {
                s.process(dt, data);
            }),
        sea::t(st::render).for_subtasks(
            [](auto& s, auto& data)
            {
                s.process(data);
            })
        );

    proxy.for_system_outputs(st::render,
        [&window](auto& s, auto& va)
        {
            window.draw(va.data(), va.size(),
                PrimitiveType::Triangles);
        });
});
```



### System execution

**System execution** stages are accessed through system implementations, using a **data proxy**.

They:

* Allow immediate execution of *non-critical operations*;

* Allow deferred execution of *critical operations*.

### Refresh {#flow_refresh}

**Refresh** stages are automatically executed after the completion of a *step stage*.

They sequentially perform the following operations:

1. Collects all deferred functions and executes them sequentially.

2. Reclaims all entities marked as "dead", making the reuse of their IDs possible.

3. Matches all newly created, destroyed and modified entities to systems, subscribing or unsubscribing them.

A **refresh state** is instantiated at the beginning of the refresh, that will be used as a buffer in order to allow communication between all refresh stages. The refresh state contains a set of entity IDs to reclaim `to_kill` and a set of entity IDs to match `to_match`.

\begin{algorithm}[H]
\caption{ECST flow: refresh algorithm overview}
\footnotesize

\SetKwData{ToKill}{toKill}
\SetKwData{ToMatch}{toMatch}
\SetKwFunction{ExecuteDeferredFunctions}{ExecuteDeferredFunctions}
\SetKwFunction{ReclaimDeadEntities}{ReclaimDeadEntities}
\SetKwFunction{MatchEntitiesToSystems}{MatchEntitiesToSystems}

    \ToKill $\longleftarrow \emptyset$\;
    \ToMatch $\longleftarrow \emptyset$\;
    \BlankLine
    \ExecuteDeferredFunctions{\ToKill, \ToMatch} \tcp*{fills \ToKill and \ToMatch}
    \ReclaimDeadEntities{\ToKill} \tcp*{mutates and reads \ToKill}
    \MatchEntitiesToSystems{\ToMatch} \tcp*{reads \ToMatch}

\end{algorithm}



#### Deferred function execution {#flow_exec_dfuncs}

As deferred functions may contain *critical operations*, they need to be executed sequentially. Deferred functions are produced during system execution - every *subtask state* has its own deferred function list.

\begin{algorithm}[H]
\caption{ECST flow: refresh - ExecuteDeferredFunctions}
\footnotesize

\SetKwData{ToKill}{toKill}
\SetKwData{ToMatch}{toMatch}
\SetKwData{I}{i}
\SetKwData{S}{s}
\SetKwData{C}{c}
\SetKwFunction{F}{F}

    \ForEach{instance \I $\in$ context \C}{
        \ForEach{state \S $\in$ instance \I}{
            \ForEach{function \F $\in$ state \S}{
                \tcc{entity deletion mutats \ToKill}
                \tcc{entity creation or component addition/removal mutates \ToMatch}
                \F{\ToKill, \ToMatch}\;
            }
        }
    }

\end{algorithm}



#### Dead entity reclamation

During system execution, entities may be marked as "dead" by subtasks. Every *subtask state* contains a *sparse set* of entity IDs marked as dead.

\begin{algorithm}[H]
\caption{ECST flow: refresh - ReclaimDeadEntities}
\footnotesize

\SetKwData{ToKill}{toKill}
\SetKwData{I}{i}
\SetKwData{S}{s}
\SetKwData{C}{c}
\SetKwData{Eid}{eid}
\SetKwFunction{F}{F}
\SetKwFunction{Unsubscribe}{Unsubscribe}
\SetKwFunction{Reclaim}{Reclaim}

    \tcc{add entities marked during system execution to \ToKill}
    \ForEach{instance \I $\in$ context \C}{
        \ForEach{state \S $\in$ instance \I}{
             \ToKill $\longleftarrow$ \ToKill $\cup$ \S.\ToKill \;
        }
    }

    \BlankLine

    \tcc{unsubscribe dead entities from systems}
    \ForEach(in parallel){instance \I $\in$ context \C}{
        \ForEach{entityID \Eid $\in$ \ToKill}{
            \Unsubscribe{\I, \Eid}\;
        }
    }

    \BlankLine

    \tcc{reclaim IDs for future use}
    \ForEach{entityID \Eid $\in$ \ToKill}{
        \C.\Reclaim{\Eid}
    }

\end{algorithm}



#### Entity-system matching

Newly created entities and entities with a mutated component set must be matched to systems. Checking if an entity matches a system is done by computing *dense bitset inclusion* between the entity's active component bitset and the system's required component bitset. Testing `std::bitset` inclusion is not part of the Standard Library *(although proposed, see [@isocpp_proposal_p0125r0])* - it can be implemented using bitwise operators as follows:

```cpp
bool matches(component_bitset cb_entity, component_bitset cb_system)
{
    return (cb_system & cb_entity) == cb_system;
}
```

A possible intuition for the code snippet above consists in thinking about systems as **keys** and entity instances as **locks**. If a key *fits in* a lock, the corresponding entity matches the system.

![ECST flow: key/lock entity/system matching intuition](source/figures/keylock.png){ #keylock width=85% }

Bitwise inclusion tests can be executed in parallel over all system instances:

\begin{algorithm}[H]

\caption{ECST flow: refresh - MatchEntitiesToSystems}
\footnotesize

\SetKwData{ToMatch}{toMatch}
\SetKwData{I}{i}
\SetKwData{C}{c}
\SetKwData{Eid}{eid}
\SetKwFunction{Matches}{Matches}
\SetKwFunction{GetComponentBitset}{GetComponentBitset}
\SetKwFunction{Subscribe}{Subscribe}
\SetKwFunction{Unsubscribe}{Unsubscribe}

    \ForEach(in parallel){instance \I $\in$ context \C}{
        \ForEach{entityID \Eid $\in$ \ToMatch}{
            \eIf{\Matches{\GetComponentBitset{\I}, \GetComponentBitset{\Eid}}}{
                \Subscribe{\I, \Eid}\;
            }{
                \Unsubscribe{\I, \Eid}\;
            }
        }
    }

\end{algorithm}