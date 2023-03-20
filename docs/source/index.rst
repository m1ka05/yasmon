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



Example
-------

Assume that we want to keep a directory in sync between two machines.
We could define a task with attributes ``src`` and ``dest`` that calls ``rsync``
upon any change in ``/tmp/dir/`` to sync with a remote host.
The ``rsync`` shell callback can use the attributes associated with a task
and thus could be reused for other tasks.

.. code-block:: yaml

   ---
   log_journal:
     level: info
   tasks:
     watch_tmp_dir:
       type: watchfiles
       changes:
         - modified
         - added
         - deleted
       callbacks:
         - rsync
       paths:
         - /tmp/dir/
       attrs:
         src: /tmp/dir/
         dest: user@host.domain.com:/tmp/dir
   callbacks:
     rsync:
       type: shell
       command:  rsync -av {src} {dest} --delete


An run would look something like

.. code-block:: shell

   $ yasmon --config ~/rsync.yaml


.. code-block::

   INFO     | yasmon.processor:load_file:20 | using config file /home/user/rsync.yaml
   INFO     | yasmon.processor:add_loggers:54 | processing loggers...
   INFO     | yasmon.cli:main:34 | 1 user loggers defined. Default stderr logger removed.
   INFO     | yasmon.callbacks:__init__:103 | rsync (<class 'yasmon.callbacks.ShellCallback'>) initialized                                                                                                                      
   INFO     | yasmon.tasks:__init__:38 | watch_tmp_dir (<class 'yasmon.tasks.WatchfilesTask'>) initialized                                                                                                                      
   INFO     | yasmon.tasks:__call__:45 | watch_tmp_dir (<class 'yasmon.tasks.WatchfilesTask'>) scheduled with rsync (<class 'yasmon.callbacks.ShellCallback'>)                                                                  
   INFO     | yasmon.callbacks:__call__:112 | rsync (<class 'yasmon.callbacks.ShellCallback'>) called by watch_tmp_dir (<class 'yasmon.tasks.WatchfilesTask'>)                                                                  
   INFO     | yasmon.callbacks:__call__:164 | callback rsync stdout:                                                                                                                                                            
     sending incremental file list                                                                                                                                                                                              
    ./                                                                                                                                                                                                                          
    added_file                                                                                                                                                                                                                  

    sent 132 bytes  received 38 bytes  340,00 bytes/sec                                                                                                                                                                         
    total size is 2  speedup is 0,01                                                                                                                                                                                            
   INFO     | yasmon.callbacks:__call__:112 | rsync (<class 'yasmon.callbacks.ShellCallback'>) called by watch_tmp_dir (<class 'yasmon.tasks.WatchfilesTask'>)                                                                  
   INFO     | yasmon.callbacks:__call__:164 | callback rsync stdout:                                                                                                                                                            
     sending incremental file list                                                                                                                                                                                              
    added_file                                                                                                                                                                                                                  

    sent 135 bytes  received 41 bytes  352,00 bytes/sec                                                                                                                                                                         
    total size is 4  speedup is 0,02                                                                                                                                                                                            
   INFO     | yasmon.callbacks:__call__:112 | rsync (<class 'yasmon.callbacks.ShellCallback'>) called by watch_tmp_dir (<class 'yasmon.tasks.WatchfilesTask'>)                                                                  
   INFO     | yasmon.callbacks:__call__:164 | callback rsync stdout:                                                                                                                                                            
     sending incremental file list                                                                                                                                                                                              
    deleting added_file                                                                                                                                                                                                         
    ./                                                                                                                                                                                                                          

    sent 60 bytes  received 33 bytes  62,00 bytes/sec                                                                                                                                                                           
    total size is 0  speedup is 0,00                                                                                                                                                                                            
