


# Encoding entities {#chapter_encoding_entities}

The *essence* of the problem that ECS solves is finding an efficient and flexible way of **encoding entities**.

After trying to define the term *"entity"*, this chapter will cover multiple entity encoding techniques, starting from **object-oriented inheritance** and gradually moving to **data-oriented composition**. To fairly compare the approaches, two example application designs will be illustrated beforehand, and then implemented with every analyzed technique.

## Definition of entity

Finding a formal and universal definition for the term *"entity"* in the context of application and game development is not an easy task. Nevertheless, a number of properties closely related to the *idea of entity* can be listed:

* An entity is something closely related to a specific concept.

* Entities have related data and related logic.

* Entities are stored, managed and processed in large quantities.

    * In addition, some particular entity instances may need to be tracked.

* Entities can be created and destroyed during program execution.

Theoretically speaking, entities could be thought of as the **fundamental building blocks** of an application. Following this line of reasoning, pattern-specific elements like components and systems, polymorphism and inheritance, or scripts and definitions in data-driven architectures may be simply considered *implementation details*.

Examples of entities include:

* **Game objects**, like **projectiles**, **walls**, and **power-ups**.

* **Widgets** in a GUI framework: **buttons**, **textboxes**, etc...

* **Client states** in a server.

* **Particles** and **lights** in VFX creation software.

It's also important to distinguish between **entity types**[^entity_types] and **entity instances**. The former is the set of properties, behaviors, aspects and ideas that all instances of a particular entity type share - like a *blueprint*. The latter refers to single instantiations of particular entity types, that can be created, tracked, destroyed, inspected and mutated.



## Example use cases

To compare the aforementioned entity encoding approaches as fairly as possible, two extremely simple hypothetical application designs will be provided in this section. A possible implementation of both designs will be shown in the following sections, in order to provide readers with example code and diagrams roughly resembling real-world applications.

Minimal designs for a fantasy **role-playing game** and a bare-bones **GUI framework** are described in the subsections below.

### Role-playing game

The designed imaginary RPG will have the following **NPCs** *(non-playing characters)*:

* A **warrior**, that can be unarmed or wield any combination of **sword** and **bow**.

* A **skeleton**.

* A flying **dragon**.

Giving the warrior the possibility of wielding a combination of weapons *(or of being unarmed)* poses interesting design decisions when creating object-oriented class hierarchies.



### GUI framework

This hypothetical GUI framework will have the following **widget** types:

* A **textbox**, which supports keyboard input.

* A **button**, which supports mouse input.

Both widget types can be **optionally animated**.

Allowing optional widget animations involves finding an optimal way of avoiding repetition or unused data/logic during entity encoding.



[^entity_types]: the word *"type"* does not necessarily refer to types in programming languages - many engines with typeless entities *(data-driven)* do exist. The intended meaning is "class of entity instances with same components that model the same concept".