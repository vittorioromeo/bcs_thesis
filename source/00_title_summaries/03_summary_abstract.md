


# Abstract {.unnumbered}

Complex real-time games and applications have to deal with enormous amounts of entities that greatly vary in behavior and constantly communicate with each other. Finding an elegant design for entity management that allows developers to quickly build applications from small composable elements, without sacrificing performance, abstraction and safety is a difficult problem - this thesis aims to solve it by designing and implementing a C++14 Entity-Component-System library *ex novo*. 

An analysis of common entity encoding techniques is presented, which pinpoints the benefits and drawbacks of approaches such as *object-oriented inheritance*, *object-oriented composition*, and *data-oriented composition*. The **Entity-Component-System** architectural pattern is examined and implemented in **ECST**, a multithreaded compile-time C++14 library. The design and implementation of the library are explored in detail, using a large number of code snippets and diagrams to aid the readers in appreciating the underlying concepts and architecture.

ECST's objective is to let developers conveniently use the Entity-Component-System pattern at compile-time, striving for maximum performance and a friendly, transparent syntax. Programmers define the high-level program logic in a declarative way, using a dataflow-oriented approach, connecting systems together to generate an implicit dependency directed acyclic graph that is automatically parallelized where possible.

Finally, an example particle simulation implemented using the presented library is analyzed and benchmarked. The components and systems used to encode the particle entities and their relationships are examined. The performance benefits of the multithreading features provided by ECST are measured.