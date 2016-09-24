WTF ?
=====

**Disclaimer:** What is stated hereafter is the result of my understanding
of the related topics. In no way this should be taken as a value assessment
of the existing works, nor as an absolute truth. Tou've been warned ;)

``nROS`` is an attempt to provide a simplified ROS (see http://www.ros.org/),
initially targeting Python based developments.

ROS itself is a tremendous achievement and there is nothing to say against
this of course, but... it is a bit too heavy and tough to learn for simple
projects.

One of the points I found boring is the lack (to my current knowledge) of a
simple deployment strategy. All the documentation I could read use the
same approach : deploy the sources on the target and issue ``catkin_make``
(or ``rosbuild`` for ROS older than ``Hydro``). This supposes that
the whole build chain is installed on the target.

There should be another path, allowing to generate binary packages
which can be quickly deployed on the targets, using usual ways such as
distribution packages (e.g. deb, RPM,...) or language related packaging tools
(e.g. setuptools, pip,...), without having to pollute them with build chains,
involving cross-compilation on the dev side if the target architecture
is different from the dev environment, or whatever other not-so-friendly stuff
for beginners.

What I find a pity with this situation is that it makes life too much
complicated for people interested by developing things in Python
for instance. They benefit from all the power of the language and its ecosystem,
from the resulting ease of development, but when it comes to deploy the result,
it starts to be a pain. Whereas it is possible to circumvent it by copying
the relevant parts of the dev trees, this is more a hack than a proven method and
I don't consider this as a production grade approach, even for hobby projects.

In addition, because a lot of job is done under the cover, ROS shows a bit
sluggish on constrained targets, even for quite powerful ones such as
Raspberry or BeagleBone. Even on comfortable laptops, a noticeable
delay can be sometimes observed between the moment an event is published by a node
and the moment a subscriber displays it.

The intent of ``nROS`` is to take inspiration from the ROS model, and
mainly from its publish/subscribe and service call approach. To avoid
re-inventing the wheel, ``nROS`` will use D-Bus for this low-level tasks.
D-Bus being natively available on many Linux distributions, even on Raspbian,
no need to worry about.

Interoperability with non-Linux worlds can be provided in various way.
The out of the box one is of course the use of the D-Bus binding available for
the involved language. Since they exists for the commonly used languages
(C/C++ and Java among others), this is not an obstacle.

An other approach uses a (to be developed) optional Web service based connector
providing a REST API for invoking services and sending signals.

Content
=======

nROS framework is intended to be distributed as a collection of
packages installed under the umbrella namespace package named ``nROS``.

This package contains the core parts of the framework and must be installed
first, since it creates the root package of the namespace.

All sub-packages must declare a dependency on it to ensure this.
