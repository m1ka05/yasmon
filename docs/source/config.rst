Configuration
=============

The config file must include ``tasks`` and ``callbacks`` dictionaries.
The former describes a collection of events to monitor and the latter a
collection of actions that can be performed upon an event. Any task can
be associatiated with any number of callbacks and any callback can be
associated with any task. Additionally, one can include ``mail`` and
``logger`` dictionaries defining mail and logger configuration.

Sample config file
------------------

.. code-block:: yaml
    :caption: ~/.config/yasmon/config.yaml

    ---
    tasks:
      task0:
        type: watchfiles
        change: deleted
        callbacks:
          - callback0
        paths:
          - /some/path/to/directory/
      task1:
        type: watchfiles
        change: modified
        callbacks:
          - callback1
          - callback2
        paths:
          - /some/path/to/file1
      task2:
        type: watchfiles
        change: deleted
        callbacks:
          - callback2
        paths:
          - /some/path/to/file2
    callbacks:
      callback0:
        type: shell
        command:  sleep 3; echo 'callback0 done'
      callback1:
        type: shell
        command:  sleep 6; echo 'callback1 done'
      callback2:
        type: shell
        command: sleep 3; echo 'callback2  done'

Callbacks
=========

Any particular callback may be used in the contex of any number of tasks.
All callbacks are executed concurrently.

Callbacks are defined in a ``callbacks`` dictionary:

.. code-block:: yaml

  callbacks:
    callback0:
      type: shell
      ...
    callback1:
      type: mail
      ...
  

ShellCallback
-------------

.. code-block:: yaml

  type: shell

PythonCallback
--------------

.. code-block:: yaml

  type: python

MailCallback
------------
.. code-block:: yaml

  type: mail



Tasks
=====

Tasks define events to be watched and associate these with callbacks.
All tasks are executed concurrently.

Tasks are defined in a ``tasks`` dictionary:

.. code-block:: yaml

  tasks:
    task0:
      type: watchfiles
      callbacks:
        - callback0
        - callback1
        - callback2
      ...
    task1:
      type: diskusage
      callbacks:
        - callback0
        - callback2
      ...
    task2:
      type: watchfiles
      callbacks:
        - callback2
      ...
  

WatchfilesTask
--------------

.. code-block:: yaml

  type: watchfiles


DiskUsageTask
-------------

.. code-block:: yaml

  type: diskusage


SystemdServiceTask
------------------

.. code-block:: yaml

  type: systemdservice


MemoryUsageTask
---------------

.. code-block:: yaml

  type: cpuusage


CpuLoadTask
-----------

.. code-block:: yaml

  type: cpuload


PingTask
-----------

.. code-block:: yaml

  type: cpuload


Logger
======


Mail
====