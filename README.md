# Scheduler
Python implementation of an XBOS-compatible scheduler.

### Purpose
This scheduler serves as a model of the scheduler component in a distributed HVAC-control system for building-scale operation built atop the BOSSWAVE platform. The system is comprised of three components, schedulers that determine a thermostat's control bounds, an arbiter that mediates between schedulers and thermostats, and the thermostats themselves.

### Structure
The scheduler is a stateless entity that reads thermostat data and publishes schedules on the scheduler's own slot and signal. It neither knows of the existence of any thermostat in particular nor of other schedulers on the system. This simplifies scheduler design as the scheduler need only focus on scheduling logic and may ignore the details of schedule propagation.

From a design perspective, the scheduler is a hierarchical collection of Single Schedule Units (SSU) which are passed into the Scheduler constructor. The Single Schedule Unit encapsulates the scheduling logic for a single perspective (the details of which are left to its creator) such as a scheduler based off of natural parameters such as time of day and time of year or a scheduler based off of social parameters like weekday vs. weekend or normal vs. holiday. This separation of logic allows for custom schedulers to be easily created through the composition of these well-defined interfaces.

The generation of a schedule will follow the flow of passing the schedule generated from one Single Schedule Unit into the Single Schedule Unit above it on the hierarchy until all desired conditions are accounted for. We can think of this flow as linked list traversal, where each link is a Single Schedule Unit. Given Single Schedule Units A and B, the order A -> B will not necessarily produce the same schedule as B -> A as one has precedence over the other.

### Creating New Schedulers
This repository contains the following:
* scheduler.py - The implementation of the overall Scheduler class. Creation of a new scheduler should not require modification to this class.
* ssu.py - The abstract Single Schedule Unit class and the Single Schedule Unit Link class (an internal structure). All Single Schedule Units must conform to the Single Schedule Unit abstract class.
* ssu_instances.py - Examples of various Single Schedule Units.

One can create new schedulers through either novel composition of existing Single Schedule Units or the creation of new Single Schedule Units (and then constructing a new Scheduler instance through composition of new and existing Single Schedule Units).

New Single Schedule Instances must conform to the following requirements:
1. Inherit from `SSU`
2. Define a `generate_schedule` method that takes the same parameters as the abstract method defined in `SSU`

Outside of these requirements, it is fine to create instance and class attributes and there is no limitation on acceptable behavior. A Single Schedule Instance may make networking calls to check the weather and so forth.
