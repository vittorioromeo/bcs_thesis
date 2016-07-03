


# Future work
ECST is in an experimental state and several design and implementation choices are subject to change. This chapter aims to provide a brief overview of the currently planned additions and adjustments.



## System instance generalization

Currently [*system instances*](#storage_system) are closely tied to the concept of entity subscription and unsubscription. In the future, a more general system instance class will be introduced that will represent a **"generic computation step"** in the depedency DAG.

Generalized system instances will have no knowledge of entities and purely act on component data: this concept, alongside specialized component storage strategies, will allow to easily deal with SIMD operations.



## Deferred function queue

[*Deferred functions*](#flow_exec_dfuncs) are implemented using `std::vector<std::function>` in the current version of ECST, introducing unnecessary run-time overhead due to dynamic allocation and polymorphism.

A specialized **"deferred function queue"** class will be introduced in the future, which will store callable objects of various size in the same resizable buffer. This will be achieved using fixed-size structures that will act as *"vtables"*, which will be stored before their corresponding callable object in the buffer. A separate lightweight index will keep track of all the vtables - iterating over them will allow efficient sequential execution of deferred functions.

Appending functions to the queue will not require any additional memory allocation.



## Declarative option map interfaces

Definining interfaces for [*option maps*](#metaprogramming_option_maps) requires the creation of a class and multiple methods which explicitly need to check option value domains and update the option map. The possibility of streamlining the definitions of compile-time option interfaces using a declarative approach will be explored in the future - the goal is to create a small code-generation library/module that will generate rich compile-time option sets with an intuitive and safe user interface.



## Streaming system outputs

Currently, a system depedendent on the output of another must wait until its parent's execution has been completed. Sometimes outputs could be processed as soon as they are generated connecting systems through a [**streaming queue**](#sys_streamqueue) - the inclusion of this feature will be investigated in the future.