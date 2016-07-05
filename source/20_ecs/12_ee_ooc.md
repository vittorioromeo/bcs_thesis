


## Object-oriented composition

A flexible way of solving the aforementioned *repetition* and *diamond* issues requires a point-of-view shift from a hierarchical approach to a **composition-based** one. Entities will be defined as containers of small reusable **behaviors**[^behaviors_vs_components], with the following characteristics:

* Behaviors **store data** and **handle logic**.

* Behavior types **conform to the same interface** and polymorphically inherit from a base `behavior` class.

* Behaviors can be added and removed from entities at run-time.

From a high-level perspective, object-oriented composition looks like this:

\dot(source/figures/generated/ecs/overview/oop_composition/example { width=85% })
(Object-oriented composition: hypotetical entity hierarchy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    BehaviorA0 [shape="rectangle", style="rounded", label="BehaviorA"]
    BehaviorB0 [shape="rectangle", style="rounded", label="BehaviorB"]
    BehaviorC0 [shape="rectangle", style="rounded", label="BehaviorC"]

    BehaviorA1 [shape="rectangle", style="rounded", label="BehaviorA"]
    BehaviorC1 [shape="rectangle", style="rounded", label="BehaviorC"]

    BehaviorA0 -> EntityA
    BehaviorB0 -> EntityA
    BehaviorC0 -> EntityA

    BehaviorA1 -> EntityB
    BehaviorC1 -> EntityB
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


### Implementation

As with the previous approach, a base class containing an application-specific `virtual` interface needs to be defined - this time the class will represent a behavior type, not an entity type.

#### Role-playing game

Here is an example on how the `skeleton` and `dragon` entities could be encoded using object-oriented composition:

\dot(source/figures/generated/ecs/overview/oop_composition/example_rpg_0)
(Object-oriented composition: RPG - skeleton and dragon)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    Physics0 [shape="rectangle", style="rounded", label="physics"]
    AI0 [shape="rectangle", style="rounded", label="ai"]
    Enemy0 [shape="rectangle", style="rounded", label="npc"]

    Physics1 [shape="rectangle", style="rounded", label="physics"]
    AI1 [shape="rectangle", style="rounded", label="ai"]
    Enemy1 [shape="rectangle", style="rounded", label="npc"]
    Flight1 [shape="rectangle", style="rounded", label="flight"]

    Physics0 -> skeleton
    AI0 -> skeleton
    Enemy0 -> skeleton

    Physics1 -> dragon
    AI1 -> dragon
    Enemy1 -> dragon
    Flight1 -> dragon
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This approach also solves the previously encountered "diamond of death" issue:

\dot(source/figures/generated/ecs/overview/oop_composition/example_rpg_1)
(Object-oriented composition: RPG - unarmed and sword+bow warrior)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    Physics0 [shape="rectangle", style="rounded", label="physics"]
    AI0 [shape="rectangle", style="rounded", label="ai"]
    Enemy0 [shape="rectangle", style="rounded", label="npc"]

    Physics2 [shape="rectangle", style="rounded", label="physics"]
    AI2 [shape="rectangle", style="rounded", label="ai"]
    Enemy2 [shape="rectangle", style="rounded", label="npc"]
    Sword2 [shape="rectangle", style="rounded", label="sword"]
    Bow2 [shape="rectangle", style="rounded", label="bow"]

    Physics0 -> warrior
    AI0 -> warrior
    Enemy0 -> warrior

    Physics2 -> sword_bow_warrior
    AI2 -> sword_bow_warrior
    Enemy2 -> sword_bow_warrior
    Sword2 -> sword_bow_warrior
    Bow2 -> sword_bow_warrior
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The code for the base polymorphic `behavior` class closely resembles the previously seen `game_object`:

```cpp
class behavior
{
public:
    virtual ~behavior() { }

    virtual void update(float dt) { }
    virtual void draw() { }
};


class physics : behavior { /* ... */ };
class ai : behavior { /* ... */ };
class npc : behavior { /* ... */ };
class flight : behavior { /* ... */ };
class sword : behavior { /* ... */ };
class bow : behavior { /* ... */ };
```

The implementation of `entity` provides an interface to manipulate behaviors at run-time, and stores the behaviors in a `std::vector` of `std::unique_ptr<behavior>`, in order to enable polymorphism to correctly take place:


```cpp
class entity
{
private:
    std::vector<std::unique_ptr<behavior>> _behaviors;

public:
    template<typename T, typename... Ts>
    auto& emplace_behavior(Ts&&... xs) { /* ... */ }

    void update(float dt)
    {
        for(auto& c : _behaviors)
            c->update(dt);
    }

    void draw()
    {
        for(auto& c : _behaviors)
            c->draw();
    }
};
```

Entity types **are not encoded as classes** anymore, but as **functions** that return entity instances:

```cpp
auto make_skeleton(/* ... */)
{
    entity result;
    result.emplace_behavior<physics>(/* ... */);
    result.emplace_behavior<ai>(/* ... */);
    result.emplace_behavior<npc>(/* ... */);

    return result;
}
```

```cpp
auto make_dragon(/* ... */)
{
    entity result;
    result.emplace_behavior<physics>(/* ... */);
    result.emplace_behavior<ai>(/* ... */);
    result.emplace_behavior<npc>(/* ... */);
    result.emplace_behavior<flight>(/* ... */);

    return result;
}
```

```cpp
auto make_sword_bow_warrior(/* ... */)
{
    entity result;
    result.emplace_behavior<physics>(/* ... */);
    result.emplace_behavior<ai>(/* ... */);
    result.emplace_behavior<npc>(/* ... */);
    result.emplace_behavior<sword>(/* ... */);
    result.emplace_behavior<bow>(/* ... */);

    return result;
}
```

#### GUI framework

This technique solves the **repetition problem** encountered during the object-oriented inheritance-based implementation of the example GUI framework.

\dot(source/figures/generated/ecs/overview/oop_composition/example_gui_0)
(Object-oriented composition: GUI entity hierarchy)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
digraph
{
    animation0 [shape="rectangle", style="rounded", label="animation"]
    keyboard0 [shape="rectangle", style="rounded", label="keyboard"]
    layout0 [shape="rectangle", style="rounded", label="layout"]

    animation1 [shape="rectangle", style="rounded", label="animation"]
    mouse1 [shape="rectangle", style="rounded", label="mouse"]
    layout1 [shape="rectangle", style="rounded", label="layout"]

    keyboard2 [shape="rectangle", style="rounded", label="keyboard"]
    layout2 [shape="rectangle", style="rounded", label="layout"]

    mouse3 [shape="rectangle", style="rounded", label="mouse"]
    layout3 [shape="rectangle", style="rounded", label="layout"]

    animation0 -> animated_textbox
    keyboard0 -> animated_textbox
    layout0 -> animated_textbox

    animation1 -> animated_button
    mouse1 -> animated_button
    layout1 -> animated_button

    keyboard2 -> static_textbox
    layout2 -> static_textbox

    mouse3 -> static_button
    layout3 -> static_button
}
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

### Communication

While entities still need to communicate with each other for the reasons described in [Chapter 3, Subsection 3.3.2](#chapter_oop_communication), this technique also may require that behaviors "talk" to one another.

Imagine implementing a `clickable` behavior for widgets:

```cpp
struct clickable : behavior
{
    bounding_box _bb;
    bool _clicked;

    void update(float) override
    {
        _clicked = mouse::overlaps(_bb);
    }
};
```

Buttons and textboxes need to "ask" the `clickable` behavior whether or not they need to handle a mouse click.

#### Address-based

A possible approach would be either checking or asserting the existence of a behavior and then access it directly through the entity. A requirement is that behaviors store a reference to their parent entity:

```cpp
class behavior
{
protected:
    entity& _entity;
    // ...
};

struct print_on_click : behavior
{
    void update(float) override
    {
        assert(_entity.has_behavior<clickable>());
        auto& bc = _entity.get_behavior<clickable>();

        if(bc._clicked) { /* ... */ }
    }
};
```

This communication method quickly becomes hard to maintain due to heavy coupling between behaviors.


#### Message-based

Similarly to the object-oriented approach, using lightweight messages and a mediator `message_queue` class can reduce coupling and make communication between behaviors much easier to manage. The implementation is essentially equivalent to the one previously shown: the base `behavior` type will provide a `virtual handle_message(const message&)` function that derived behavior types can override.



### Advantages and disadvantages

Object-oriented composition is easy to implement and much more flexible than the hierarchical approach, but it's still suboptimal compared to data-oriented composition:

* No separation of data and logic is present.

* There is a significant overhead due to run-time polymorphism.

* It's still impossible to take advantage of the CPU cache.

A crucial piece of the ECS pattern, the **system**, is still missing from this technique. Its introduction will allow a clean separation of data and logic, that will lead to parallelization opportunities and possible cache-friendliness. The introduction of the system will allow to replace behaviors with logic-less **components**.



[^behaviors_vs_components]: the term **"behavior"** is being used instead of **"component"** in order to clearly distinguish the two concepts, as the former contains and handles logic, in contrast to the latter.