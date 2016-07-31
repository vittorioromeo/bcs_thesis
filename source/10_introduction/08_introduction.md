


# Introduction

Successful development of complex real-time applications and games requires a flexible and efficient **entity management** system. As a project becomes more intricate, it's critical to find an elegant way to compose objects in order to prevent code repetition, improve modularity and open up powerful optimization possibilities.

The **Entity-Component-System** architectural pattern was designed to achieve the aforementioned benefits, by **separating data from logic**.

* Entities[^entities] can be composed of small, reusable, and generic components;

* Components can be stored in contiguous memory areas, thus improving **data locality** and **cache-friendliness**;

* Application logic can be **easily parallelized** and abstracted away from the objects themselves and their storage policies;

* The state of the application can be serialized and shared over the network with less effort;

* A more modular, generic and easily-testable codebase.

The **ECS**[^ecs] pattern will be described and explained in this thesis, alongside an in-depth design and implementation analysis of **ECST**, a **C++14 multithreaded compile-time[^compile_time_ecs] Entity-Component-System** library.



## Problem/background

Consider a traditional **object-oriented** architecture for a complex application or game: base object classes are defined as roots of huge hierarchies, from which entities derive, containing both data and logic. With the addition of new entity types, the complexity of the code increases, while code reusability, flexibility and performance decrease.

An alternative, more powerful approach consists in using **data-oriented design**[^data_oriented_design] *(DOD)* and **composition**[^composition], where the code is designed around the data and its flow[^flow], and entities are defined as aggregates of **components**. Data and logic are separated in this approach: auxiliary classes or procedures process data without reasoning in terms of objects, opening up opportunities for functionally pure computations and parallelism. DOD also lends itself to **cache-friendliness**, as storing data separately allows developers to make use of contiguous memory storage.

One common complaint regarding the *DOD + composition* approach is that it seems **less convenient** and **less safe** than an object-oriented approach. While developers praise the flexibility and performance benefits obtained by the aforementioned techniques, those praises are often accompanied by the idea that **abstraction** and **encapsulation** have to be sacrificed in order to get the benefits those techniques aim to achieve.


### Objectives

* Objectively analyze **object-oriented design** techniques versus **data-oriented design** + **composition**.

    * A *by-example* examination of a gradual approach shift (from object-oriented inheritance to data-oriented composition) will be presented in [Part 1](#ecs_part_overview).

* Analyze the design, architecture and implementation of **ECST**, a C++14 compile-time Entity-Component-System library, developed as the thesis project, in [Part 2](#part2_ecst).

    * Prove that it's not necessary to sacrifice typical OOP advantages (like encapsulation or code reusability), thanks to C++14 **cost-free abstractions** that make use of compile-time knowledge to increase productivity, safety, maintainability and code quality.

* Examine the design and implementation of a simple **real-time particle simulation** developed using ECST in [Part 3](#part3_sim).

    * Various combination multithreading compile-time options will be compared through benchmarks.


## Related literature

Literature on the Entity-Component-System pattern is limited and hard to find. On the contrary, entity management, especially in the context of game development, has been extensively covered: see [@gregory2014game, chapters 14 and 15], [@game_programming_gems_4, section 1.8], [@game_programming_gems_5, section 1.3], [@game_programming_gems_6, section 4.6], and [@doherty2003software]. Heavily composition-based approaches can be found in [@Wiebusch:2012] and in [@6658092]

Countless online articles and blog posts on the ECS pattern and on data-oriented design have been written - AAA projects postmortems, presentations, well-documented libraries and other kind of valuable resources can be easily found. An excellent introduction to composition can be found in [@robertnystorm_gpp_component]. One of the most comprehensive sets of articles on entity systems was written by Adam Martin, and can be found in [@tmachine_es_category].



## Code

ECST's source code can be found in the following GitHub repository under the *Academic Free License ("AFL") v. 3.0*: [https://github.com/SuperV1234/ecst](https://github.com/SuperV1234/ecst). The source code for the thesis and for the example particle simulation can be found in the following GitHub repository under the *Academic Free License ("AFL") v. 3.0*: [https://github.com/SuperV1234/bcs_thesis](https://github.com/SuperV1234/bcs_thesis).

*Note to readers:* most of the code snippets included in the thesis are simplified in order to make them more easily understandable and less cluttered. Features like `noexcept` and boilerplate code like repeated *ref-qualified* member functions are intentionally not included. From [Part 2] onwards, the reader is expected to be familiar with advanced C++11 and C++14 features.



## Long-term research

Research on the Entity-Component-System pattern and its possible implementations has been a long-term personal project for the thesis author:

* [SSVEntitySystem](https://github.com/SuperV1234/SSVEntitySystem), a naive implementation of a single-threaded ECS making use of run-time polymorphism, was released as an open-source library in 2012;

* A singlethreaded compile-time Entity-Component-System implementation tutorial talk was presented at [CppCon 2015](http://cppcon.org) *(Bellevue, WA)*. All material used during the talk is available in the following GitHub repository: [https://github.com/SuperV1234/cppcon2015](https://github.com/SuperV1234/cppcon2015);

* Development of ECST started in December 2015. An earlier version of the library was presented in May 2016 at [C++Now 2016](http://cppnow.org) *(Aspen, CO)*. The material used during the presentation is available in the following GitHub repository: [https://github.com/SuperV1234/cppnow2016](https://github.com/SuperV1234/cppnow2016).



[^entities]: core building blocks of an application.

[^ecs]: Entity-Component-System.

[^data_oriented_design]: development approach where "it's all about the data", which drives the programmer to design the code around the data. Can provide significant performance and reusability benefits.

[^composition]: avoidance of polymorphic hierarchies in favor of multiple reusable small pieces of data and/or logic that, when put together, form entities.

[^flow]: set of chained data transformations that may depend on each other.

[^compile_time_ecs]: *"compile-time"*, in this context, means that component types and system types are known during compilation (i.e. not data-driven).