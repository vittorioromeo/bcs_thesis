


## Object-oriented inheritance

A reasonably easy way of encoding entities consists in using a **hierarchy of polymorphic objects** - this technique *feels natural* to developers accustomed to OOP principles. The concepts of *"component"* and *"system"* will not appear in this approach: both **data** and **logic** are stored inside entities. Entity types encoded using this technique produce hierarchy graphs similar to the following one:

\dot(source/figures/generated/ecs/overview/oop/example_hierarchy_0 { width=65% })
(Object-oriented inheritance: hypothetical entity hierarchy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=BT

    EntityA -> BaseEntity
    EntityB -> BaseEntity
    EntityC -> BaseEntity
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Implementation

This approach does not require any technique-specific implementation detail. Since entity types have to conform to the same interface *(due to the use of run-time polymorphism)*, the *"base entity"* class is defined directly in the application's codebase. The provided `virtual` interface greatly depends on the application itself. Some sort of *"manager"* class is usually defined as well, which keeps track of the active entities and provides a convenient interface to perform actions on them.

#### Role-playing game

To simulate the implementation of the example RPG, a hypothetical class hierarchy is shown below:

\dot(source/figures/generated/ecs/overview/oop/example_hierarchy_rpg { width=70% })
(Object-oriented inheritance: RPG entity hierarchy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=BT

    physics_body -> game_object
    npc -> physics_body
    skeleton -> npc
    dragon -> npc
    warrior -> npc
    sword_warrior -> warrior
    bow_warrior -> warrior
    sword_bow_warrior -> sword_warrior
    sword_bow_warrior -> bow_warrior
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The `game_object` entity type will be the base class from which all other game objects derive - the interface has to be defined there:

```cpp
class game_object
{
public:
    virtual ~game_object() { }

    virtual void update(float dt) = 0;
    virtual void draw() = 0;
};
```

The rest of the hierarchy is built upon `game_object`, **incrementally** adding data and logic. Every game object that follows the laws of physics will inherit from `physics_body`:

```cpp
class physics_body : game_object
{
private:
    vector2f _position, _velocity;

public:
    void update(float dt) override
    {
        _position += _velocity * dt;
    }
};
```

Physical objects that can be rendered and controlled by an AI will inherit from `npc`:

```cpp
class npc : physics_body
{
private:
    model* _model;
    texture* _texture;
    ai* _ai;

public:
    void update(float dt) override
    {
        physics_body::update(dt);
        _ai->think(dt);
    }

    void draw() override { /* ... */ }
};
```

The leaves of the hierarchy tree will contain highly-specific data and logic:

```cpp
class skeleton : npc { /* ... */ };
class dragon : npc { /* ... */ };
class warrior : npc { /* ... */ };

class sword_warrior : virtual warrior { /* ... */ };
class bow_warrior : virtual warrior { /* ... */ };

class sword_bow_warrior : sword_warrior, bow_warrior
{
    /* ... */
};
```

To avoid code repetition during the implementation of a warrior that simultaneously uses both a sword and a bow, a situation that requires *multiple inheritance* arises. A possible way of avoiding duplicating the contents of the `warrior` class twice in `sword_bow_warrior` is using C++'s `virtual` inheritance feature, concisely explained in [@cppreference_virtual_base_classes]. These kind of hierarchies making use of multiple inheritance are extremely cumbersome to maintain and expand: the pattern appearing in `sword_bow_warrior` is in fact commonly called *"diamond of death"*.

##### "Diamond of death"

The **"diamond of death"** *(a.k.a. "deadly diamond" or "common ancestor" issue)* is a well-known problem that can appear in object-oriented hierarchies. It was comprehensively covered in [@truyen2004generalization]. An example is found in this part of the previous hierarchy:

\dot(source/figures/generated/ecs/overview/oop/diamond_of_death { width=85% })
(OOP encoding issue: "diamond of death")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=RL

    warrior -> npc
    sword_warrior -> warrior
    bow_warrior -> warrior
    sword_bow_warrior -> sword_warrior
    sword_bow_warrior -> bow_warrior
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The hierarchy causes **ambiguity** in case both `sword_warrior` and `bow_warrior` override the same method in `warrior` and causes **duplication** of `warrior`'s fields in `sword_bow_warrior`. To solve these problems, unless a feature like C++'s `virtual` inheritance is used, the class hierarchy has to be altered to avoid the "diamond", potentially introducing code repetition.

#### GUI framework

An example implementation of the previously described imaginary GUI framework will now be covered. As with the role-playing game, the proper starting point is the class hierarchy. The base class of the framework will be called `widget`. Unfortunately, the feature that allows widgets to be optionally animated impedes the creation of a straightforward diagram and introduces the **repetition problem**.

##### Repetition problem

Handling optional animation features is problematic: a possible approach would be defining a base `animated_widget` class and have all widgets derive from it.

\dot(source/figures/generated/ecs/overview/oop/repetition_problem_0 { width=75% })
(OOP encoding issue: repetition #0)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=RL

    animated_widget -> widget
    textbox -> animated_widget
    button -> animated_widget
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In the case shown above, all instances of `textbox` and `button` will have potentially unnecessary fields and methods if they do not make use of the framework's animation capabilities. To solve this, one may try to restructure the hierarchy as follows:

\dot(source/figures/generated/ecs/overview/oop/repetition_problem_1)
(OOP encoding issue: repetition #1)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=BT

    animated_widget -> widget
    static_widget -> widget
    static_textbox -> static_widget
    static_button -> static_widget
    animated_textbox -> animated_widget
    animated_button -> animated_widget
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Or in the following way:

\dot(source/figures/generated/ecs/overview/oop/repetition_problem_2 { width=70% })
(OOP encoding issue: repetition #2)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    rankdir=BT

    textbox -> widget
    button -> widget
    animated_textbox -> textbox
    animated_button -> button
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

As the graphs show, **there is always some form of repetition in one way or another**:

* In the first hierarchy, the widget data/logic for `textbox` and `button` has to be repeated for the `static_widget` and `animated_widget` branches of the hierarchies.

* In the second hierarchy, the animation data/logic has to be repeated both for `textbox` and `button`.

Upon deciding between one of the hierarchies, the implementation does not differ much from the RPG one: a `widget` base class will be created, with an interface all derived widgets must conform to. The derived widget types will override `widget`'s methods to implement their logic.


### Communication {#chapter_oop_communication}

Entity communication in this approach may need to occur for several reasons, including:

* One entity needs to notify another entity about a particular event.

    * *Example:* the close button entity needs to inform the parent window that it needs to be closed.

    * *Example:* a ball hitting a brick in a Breakout clone needs to destroy the brick.

* An entity may be an aggregate of entities that need to cooperate.

    * *Example:* a `tank` entity may be "composed" by a `cannon` entity and a `tracks` entity.

#### Address-based

Since entities are dynamically allocated, their location in memory does not change during program execution. Senders that are **aware of the lifetimes of their listeners** can effectively store pointers *(or references)* to them, in order to directly execute some of their methods or mutate their `public` fields.

```cpp
class window : widget { /* ... */ };

class close_button : widget
{
private:
    window& _parent;

    // ...initialize fields on construction...

    void click()
    {
        _parent.close();
    }
};
```

If senders are not aware of how long their receivers will live, or if senders need to conditionally execute code depending on whether or not a specific receiver is alive, this approach fails. Additional drawbacks include harder networking and serialization, tightly coupled code which is hard to reason about, and lack of flexibility. A possible alternative given by the introduction of a *mediator* class that deals with entity creation and destruction, keeping track of entity states.

The mediator could generate **handles** that, similarly to pointers, would allow access to entities' memory locations, but also add an additional layer of indirection where the validity of the entity pointed to by the handle can be checked.


#### Subscription-based

Using a pattern similar to **"signals and slots"** or **"events and delegates"**, it is possible to implement inter-entity communication by subscribing/unsubscribing to events and implementing event handlers. This approach solves the problem where the sender is not aware of the lifetime of the receiver - the onus of subscribing to specific event types lies on the receiver, that can unsubscribe itself upon destruction.

The `game_object` class will contain an `on_destruction` event that will be invoked on entity destruction:

```cpp
class game_object
{
public:
    event on_destruction;
    // ...
};
```

Game objects that need to communicate, like `tank`, will provide subscribable events:

```cpp
class cannon : game_object { /* ... */ };
class tracks : game_object { /* ... */ };

class tank : game_object
{
public:
    event on_fire;
    // ...
};
```

Entities will be *"linked"* together after they have been created:

```cpp
void link_tank_events(tank& tk, cannon& cn, tracks& ts)
{
    auto event_handle = tk.on_fire.subscribe([&]
        {
            ts.stop();
            cn.fire();
        });

    auto unsub_on_fire = [&tk, event_handle]
        {
            tk.on_fire.unsubscribe(event_handle);
        };

    cn.on_destruction(unsub_on_fire);
    ts.on_destruction(unsub_on_fire);
}
```

While this approach provides some decoupling between entity types, it also introduces unnecessary run-time overhead due to event management. It is also unsafe, as application code needs to make sure entities with subscribers outlive their subscribers *(e.g. `tk` needs to outlive both `cn` and `ts`)*.


#### Message-based

A superior technique, that decouples entity communication from the entities themselves, consists in **producers** generating **messages** that are forwarded to a **message queue** and read by **consumers**. Message types can be implemented as a **tagged** `union` of lightweight structs, by using run-time polymorphism, or by using a variant type like `boost::variant`:

```cpp
struct maximize_message { int _window_id; };
struct close_message { int _window_id; };

using message = variant<maximize_message, close_message>;
```

After modeling the union of message types, the base entity class will need to provide a `virtual` event handler method:

```cpp
class widget
{
protected:
    virtual handle_message(const message&) { }
    // ...
}
```

Entities can create messages by enqueuing them in a shared `message_queue` object:

```cpp
class close_button : widget
{
private:
    int _parent_id;

    void click(message_queue& mq)
    {
        mq.enqueue(message{close_message{_parent_id}})
    }

    // ...
};
```

Derived classes can override the event handler method to respond to messages:

```cpp
class window : widget
{
private:
    int _id;

    void handle_message(const message& m) override
    {
        visit(m,
            [this](const maximize_message& x)
            {
                if(x._window_id == this->_id)
                    this->maximize();
            },
            [this](const close_message& x)
            {
                if(x._window_id == this->_id)
                    this->close();
            });
    }

    // ...
};
```

This approach is versatile and can be implemented more cleverly and efficiently, although it is rarely used outside of huge-scale projects in practice. Entities never explicitly know about each other - they "subscribe" to particular message types instead and process them as they arrive. When a sender or receiver entity is destroyed, it simply stops sending or receiving messages, preventing erroneous memory accesses.



### Advantages and disadvantages

Compared to a completely *unstructured* approach, using polymorphic objects to encode entities provides a cleaner and simpler way of managing data and logic. However, the object-oriented inheritance technique is only suitable for simple applications and games with a limited amount of entity types and a small number of active entity instances at run-time. Its main selling point is the ease of development and programming productivity.

The use of polymorphism negatively impacts performance and memory usage in comparison to a data-oriented approach, especially because it makes taking advantage of data locality and cache-friendliness impossible[^cache_friendliness_impossible].

Using inheritance to build an entity type hierarchy lacks flexibility and, as seen in the examples, introduces significant architectural problems.

[^cache_friendliness_impossible]: common reasons include: indirection and size overhead caused by dynamic allocation; loading unused fields in the cache. More information at [@ithare_allocations] and [@scee_oop_pitfalls].