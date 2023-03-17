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
   * Runnable as a :doc:`system service <service/service>`
   * Concurrent execution of tasks and callbacks
   * Task attributes for callback parameters
   * Repurposable callbacks


Tasks
-----

   * Monitoring file and directory changes, :class:`yasmon.tasks.WatchfilesTask`
   * |:construction:| Monitoring disk usage, :class:`yasmon.tasks.DiskUsageTask`
   * |:construction:| Monitoring general shell commands, :class:`yasmon.tasks.ShellTask`
   * |:construction:| Monitoring general python scripts, :class:`yasmon.tasks.PythonTask`
   * |:construction:| Monitoring file permissions, :class:`yasmon.tasks.FilePermissionsTask`
   * |:construction:| Monitoring systemd services, :class:`yasmon.tasks.SystemdServiceTask`
   * |:construction:| Monitoring memory usage, :class:`yasmon.tasks.MemoryUsageTask`
   * |:construction:| Monitoring cpu load, :class:`yasmon.tasks.CpuLoadTask`
   * |:construction:| Monitoring ping, :class:`yasmon.tasks.PingTask`

Callbacks
---------

   * Shell commands, :class:`yasmon.callbacks.ShellCallback`
   * Logger callback, :class:`yasmon.callbacks.LoggerCallback`
   * |:construction:| Python scripts, :class:`yasmon.callbacks.PythonCallback`
   * |:construction:| Mail notifications, :class:`yasmon.callbacks.MailCallback`

.. toctree::
   :caption: Run as service
   :hidden:

   service/service
   service/config

.. toctree::
   :caption: API
   :hidden:

   api/callbacks
   api/tasks


