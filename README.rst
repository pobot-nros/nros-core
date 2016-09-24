WTF ?
=====

``nROS`` is a simplified ROS (see http://www.ros.org/), initially
targeting Python based developments.

ROS is a tremendous achievement and there is nothing to say against
this of course, but... it is a bit too heavy and tough to learn for simple
projects.

One of the points I found boring is the lack (to my knowledge) of a
simple deployment strategy. All the documentation I could read use the
same approach : deploy the sources on the target and issue ``catkin_make``
(or ``rosbuild`` for ROS older than ``Hydro``). This supposes that
the whole build chain is installed on the target.

There should be another path, allowing to generate binary pakages
which can be quickly deployed on the targets and without having to
pollute them with build tools, involving cross-compilation on the
dev side if the target architecture is different from the dev environment.

The nasty point with this situation is that it makes life too much
complicated for people interested only in developing things in Python
for instance. It is possible to circumvent it by copying the relevant parts
of the dev trees, but this is more a hack than a proven method.

In addition, because a lot of job is done under the cover, ROS shows a bit
sluggish on constraint targets, even for quite powerful ones such as
Raspberry or BeagleBoneBlack. Even on comfortable laptops, a noticeable
delay can be sometimes observed between the moment an event is published by a node
and the moment a subscriber displays it.

The intent of ``nROS`` is to take inspiration from the ROS model, and
mainly from its publish/subscribe and service call approach. To avoid
re-inventing the wheel, ``nROS`` will use D-Bus for this task. D-Bus
being natively available on most Linux distributions, even on Raspbian,
no need to worry about.

Interoperability with non-Linux worlds is provided by the mean of
a Web services based gateway, added by an optional package to avoid
weighing down configurations not needing such a support.

Content
=======

nROS framework is intended to be distributed as a collection of
packages installed under the umbrella namespace package named ``nROS``.

This package contains the core parts of the framework and must be installed
first, since it creates the root package of the namespace.

All sub-packages must declare a dependency on it to ensure this.
