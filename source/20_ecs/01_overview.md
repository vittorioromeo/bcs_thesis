


# Overview {#ecs_part_overview}

**Entity-component-system** *(ECS)* is a software development architectural pattern suited for complex applications and games that benefit from defining objects in terms of smaller, reusable parts. The ECS pattern embraces the **"composition over inheritance"** principle, solving the issues caused by deep inheritance hierarchies and introducing significant **performance**, **flexibility** and **productivity** advantages.

The pattern consists of three elements that interact with each other:

* **Entities**: defined by Adam Martin in [@tmachine_esmmogfuturep2_2007] as "fundamental conceptual building blocks" of a system, which represent concrete application objects. They have no application-specific data or logic.

* **Components**: small, reusable, types that compose entities. Again, citing Adam Martin in [@tmachine_esmmogfuturep2_2007], a component type "labels an entity as possessing a particular aspect". Components store data but do not contain any logic.

* **Systems**[^systems_processors]: providers of implementation logic for entities possessing a specific set of component types.

In this chapter, the history and some use-cases of the Entity-Component-System pattern will be briefly explored. Afterwards, in [Chapter 3](#chapter_encoding_entities), a gradual transition of **entity encoding** techniques, from *"traditional" object-oriented inheritance* to a *data-oriented*[^data_oriented_vs_data_driven] approach, will be shown and analyzed.





## History and use cases

The Entity-Component-System pattern is heavily used today, especially in AAA game development.

One of the earliest uses of a composition-based architectural pattern in AAA game development can be found in **Thief: The Dark Project (1998)** [@tomleonard_thiefpostmortem_1999], where the usage of a data-driven system focused on the creation of small reusable game engine components was considered a "risk" that paid off in terms of productivity and quality of the end product.

A similar data-driven component-based approach was implemented in **Dungeon Siege (2002)** - Scott Bilas, one of the engine developers, explained the techniques used in **A Data-Driven Game Object System** at GDC San Jose 2002 [@scottbilas_dungeonsiege_2002].

Many similar lectures or project postmortems can be found, praising the benefits of composition and the additional productivity provided by data-driven development. Of notable interest, **Evolve Your Hierarchy** [@mickwest_evolveyourhierarchy_2007], by Mick West, is an article written in 2007 that clearly shows the advantages of composition over inheritance, and was a well-received introduction to the ECS pattern for many game developers.

Another excellent example can be found in Terrance Cohen *(Insomniac Games)*'s **A Dynamic Component Architecture for High Performance Gameplay** GDC Canada 2010 lecture [@terrancecohen_dynamiccomparchitecture_2010].

While academic papers and publications on the subject are rare to find, there currently are countless reports and case studies of successful uses of the ECS pattern in games and applications, ranging from VFX and computer graphics [@stackexchange_ixe_answer], to independent *roguelike* game development [@sproggiwood_irdc_2015_talk].



[^systems_processors]: a.k.a. **processors**.

[^data_oriented_vs_data_driven]: **data-oriented** design is a development technique that primarily focuses on data *(instead of objects)*, separated from logic. The code is designed around the data, potentially resulting in a more efficient *(due to cache-locality, easier parallelization opportunities and lack of polymorphism overhead)* implementation. Data-oriented design is orthogonal to **data-driven** programming, which is a paradigm where the flow of the program is controlled by external data at run-time.