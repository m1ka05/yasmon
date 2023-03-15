Yasmon - Yet Another System Monitor
===================================

|docs| |coverage|

.. |docs| image:: https://yasmon.mika.sh/docs.svg
   :target: https://yasmon.mika.sh/

.. |coverage| image:: https://yasmon.mika.sh/coverage/coverage.svg
   :target: https://yasmon.mika.sh/coverage/


Yet Another System Monitor written in Python with flexible and extensible
tasks and callbacks, as well as proper logging facilities. Written with
Python 3.11 onwards in mind.

Design choices
--------------

* Configuration in a single YAML file
* Detailed logging to system journal
* Run as a system service
* Concurrent execution of tasks and callbacks
* Task-independent callbacks with template parameters


Tasks
-----

* Monitoring file and directory changes
* (TODO) Monitoring disk usage
* (TODO) Monitoring general shell commands
* (TODO) Monitoring general python scripts
* (TODO) Monitoring file permissions
* (TODO) Monitoring systemd services
* (TODO) Monitoring memory usage
* (TODO) Monitoring cpu load
* (TODO) Monitoring ping

Callbacks
---------

* Shell commands
* (TODO) Python scripts
* (TODO) Mail notifications
