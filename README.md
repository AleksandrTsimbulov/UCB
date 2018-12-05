Made by Aleksandr Tsimbulov in 03.12.2018 edited 06.12.2008
Contacts: worktda@yandex.ru

Service provides an API for creation, changing and deleting records to/from classifier type structures.
Service works on local machine at http://0.0.0.0:10000/api. No frontend servers/services is implemented.
For api description/checking proceed to the following url: http://0.0.0.0:10000/ui

Service uses mongodb and python-3.6 alpine docker images.

In order to build and run the service execute the following commands in the shell:
$ docker-compose build
$ docker-compose up