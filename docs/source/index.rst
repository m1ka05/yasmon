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
   * |:construction:| Monitoring general shell commands, :class:`yasmon.tasks.ShellTask`
   * |:construction:| Monitoring disk usage, :class:`yasmon.tasks.DiskUsageTask`
   * |:construction:| Monitoring systemd services, :class:`yasmon.tasks.SystemdServiceTask`
   * |:construction:| Monitoring memory usage, :class:`yasmon.tasks.MemoryUsageTask`
   * |:construction:| Monitoring cpu load, :class:`yasmon.tasks.CpuLoadTask`
   * |:construction:| Monitoring file permissions, :class:`yasmon.tasks.FilePermissionsTask`
   * |:construction:| Monitoring ping, :class:`yasmon.tasks.PingTask`

Callbacks
---------

   * Shell commands, :class:`yasmon.callbacks.ShellCallback`
   * Logger callback, :class:`yasmon.callbacks.LoggerCallback`
   * Mail notifications, :class:`yasmon.callbacks.MailCallback`

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



Example
-------

Assume that we want to keep a directory in sync between two machines.
We could define a task with attributes ``src`` and ``dest`` that calls ``rsync``
upon any change in ``/tmp/dir/`` to sync with a remote host.
The ``rsync`` shell callback can use the attributes associated with a task
and thus could be reused for other tasks. Additionally, we want to send an email
to report on changes and attach a log file.

.. code-block:: yaml

   ---
   log_journal:
     level: info
   log_file:
     level: debug
     path: /tmp/yasmon.log
   tasks:
     directory_monitor:
       type: watchfiles
       changes:
         - modified
         - added
         - deleted
       callbacks:
         - rsync
         - mail_report
       paths:
         - /tmp/dir/
       attrs:
         src: /tmp/dir/
         dest: user@host.domain.com:/tmp/dir
   callbacks:
     rsync:
       type: shell
       command:  rsync -av {src} {dest} --delete
     mail_report:
       type: mail
       host: smtp.server.com
       port: 587
       login: user@server.com
       password: password
       security: starttls
       from: user@server.com
       to: destination@another.com
       subject: "Yasmon notification"
       message: |
         Yasmon
         ======

         Directory monitor reports: {path} has been {change}.
         Running sync...
       attach:
         - /tmp/yasmon.log
       delay: 10

