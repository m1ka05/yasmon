Yasmon - Yet Another System Monitor
===================================

|ci| |docs| |coverage|

.. |ci| image:: https://github.com/m1ka05/yasmon/actions/workflows/main.yml/badge.svg?branch=main
   :target: https://github.com/m1ka05/yasmon/actions/workflows/main.yml

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
* Runnable as a system service
* Concurrent execution of tasks and callbacks
* Task attributes for callback parameters
* Repurposable callbacks
