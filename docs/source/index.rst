Welcome to Yasmon's documentation!
===================================
|ci| |docs| |coverage|

.. |ci| image:: https://github.com/m1ka05/yasmon/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/m1ka05/yasmon/actions/workflows/main.yml

.. |docs| image:: https://yasmon.mika.sh/docs.svg
   :target: https://yasmon.mika.sh/

.. |coverage| image:: https://yasmon.mika.sh/coverage/coverage.svg
   :target: https://yasmon.mika.sh/coverage/

----


Yet Another System Monitor written in Python with flexible and extensible
tasks and callbacks, as well as proper logging facilities. Written with
Python 3.11 onwards in mind.

Design choices
--------------

   * Configuration in a single :doc:`YAML file <service/config>`
   * Detailed logging to system journal
   * Run as a :doc:`system service <service/service>`
   * Concurrent execution of tasks and callbacks
   * Task-independent callbacks with template parameters


Tasks
-----

   * Monitoring file and directory changes, :class:`yasmon.tasks.WatchfilesTask`
   * (TODO) Monitoring disk usage, :class:`yasmon.tasks.DiskUsageTask`
   * (TODO) Monitoring general shell commands, :class:`yasmon.tasks.ShellTask`
   * (TODO) Monitoring general python scripts, :class:`yasmon.tasks.PythonTask`
   * (TODO) Monitoring file permissions, :class:`yasmon.tasks.FilePermissionsTask`
   * (TODO) Monitoring systemd services, :class:`yasmon.tasks.SystemdServiceTask`
   * (TODO) Monitoring memory usage, :class:`yasmon.tasks.MemoryUsageTask`
   * (TODO) Monitoring cpu load, :class:`yasmon.tasks.CpuLoadTask`
   * (TODO) Monitoring ping, :class:`yasmon.tasks.PingTask`

Callbacks
---------

   * Shell commands, :class:`yasmon.callbacks.ShellCallback`
   * (TODO) Python scripts, :class:`yasmon.callbacks.PythonCallback`
   * (TODO) Mail notifications, :class:`yasmon.callbacks.MailCallback`

.. toctree::
   :caption: Run as service
   :maxdepth: 5
   :hidden:

   service/service
   service/config

.. toctree::
   :caption: API
   :maxdepth: 5
   :hidden:

   api/callbacks
   api/tasks


