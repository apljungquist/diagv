# Replayable App Framework

## Goals
The primary goal of this package is to facilitate building data processing apps with emphasis on
* Flexibility - the app can be reconfigured for debugging, development or different purpose
* Intelligibility - it is easy to understand what the app will do
* Replayability - the app behavior can be reproduced using data captured in previous runs

## Usage
Look in `examples/simple.py` for a toy simple app that demonstrates how the package can be used.

## Problems
Many opportunities for improvement can be foreseen but have not been implemented because
* a lack of time,
* insufficient value, or
* excessive cost.

This section documents what they are and some ideas around how to implement them.

### Shared, mutable state
If a node mutates its inputs it may affect other nodes that also received the same input.
Sometimes this behavior is intentional (optimization, laziness) and sometimes it is accidental (bug).
It is hard in python to enforce immutability, so it may be hard for the framework to help prevent accidental mutation.
In the case of intentional mutation the framework could help by establishing patterns and providing utilities.
Ideas include:
* Declaring mutability as part of type, serving readers before any writer and refusing multiple writers.
* Providing read-write lock primitives for which the write lock cannot be released.

### Latency
Latency is a problem for a graph in which the nodes interact directly, not via the engine.
If the latency for one node exceeds the update interval then the graph cannot keep up.
When the engine mediates it can start the next update before the previous has completed while preserving causality.
It could even buffer the data if the latency is much higher than the interval.
However, concurrency increases the risk of bugs if functions have shared, mutable state.