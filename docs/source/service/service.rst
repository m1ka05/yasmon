Systemd Service
===============

A simple systemd unit file for an Yasmon user service could be

.. code-block:: shell

    # file: ~/.config/systemd/user/yasmon.service
    [Unit]
    Description=Yet Another System Monitor
    After=network.target

    [Service]
    Type=simple
    SyslogIdentifier=yasmon
    ExecStart=/usr/bin/env python3 /home/$USER/.local/bin/yasmon

    [Install]
    WantedBy=default.target


The default location of the config file is ``~/.config/yasmon/config.yaml``. The user service can be
enabled and startet by

.. code:: shell

    $ systemctl --user --now enable yasmon


For journal logs one can use

.. code:: shell

    $ journalctl --user -fb -u yasmon.service 


CLI
---

Although Yasmon is primarly designed to be run as a monitoring service accompanied by proper logging,
it can be also run from commandline with some options:

.. code-block:: shell

    $ yasmon -h
    usage: yasmon [-h] config

    positional arguments:
      config      yaml config file path

    options:
      -h, --help  show this help message and exit




