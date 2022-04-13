<h1><center>OpenNetLab</center></h1>

+ [OVERVIEW](#overview)
	+ [previous works](#previous-works)
	+ [goal of OpenNetLab](#goal-of-opennetlab)
+ [DESIGN](#design)
	+ [OpenNetLab framework](#opennetlab-framework)
	+ [Crotroller](#crotroller)
		+ [frontend and backend](#frontend-and-backend)
		+ [storage](#storage)
		+ [resource management and task dispatch](#resource-management-and-task-dispatch)
	+ [experiment running code](#experiment-running-code)
+ [IMPLEMENTATION](#implementation)
	+ [OpenNetLab framework](#opennetlab-framework)
	+ [design a new lab](#design-a-new-lab)
+ [override the callback when receiving packet from client](#override-the-callback-when-receiving-packet-from-client)
+ [override the handler to process test case and send packets to server](#override-the-handler-to-process-test-case-and-send-packets-to-server)
+ [TIME SCHEDULE](#time-schedule)

## OVERVIEW

### previous works

We’ve looked through the previous projects and platforms, summarizing their characteristics
as follows:

1. Open Networking Lab: carried out by the Open University Faculty of Science, Technology,
Engineering and Mathematics (STEM) and is funded by the Ufi VocTech Trust
2. CCNA Labs: simulator for Network routing experiment
3. PNETLab: PNETLab Box virtual machine offers packet network emulator tool

### goal of OpenNetLab

1. Build a programmable platform which provides a list of basic network experiments, which
is easy to configure and use in university network course.
2. New experiments can be designed easily on top of OpenNetLab framework.
3. Visualization of the experiment process, which helps students to understand network con-
cepts.
4. Extensibility and stability, more nodes can be add into OpenNetLab.

## DESIGN

### OpenNetLab framework

OpenNetLab is encapsulated into a python package and provides the following functionalities:
* basic client and server node
* p2p node
* system components
  * logger
  * evaluator
  * utilities

### Crotroller

#### frontend and backend

* vue: frontend framework.
* django: a MVC web backend framework, which makes it convenient for developers to carry out follow-up maintenance and expansion.
* nginx: proxy for static resource and achieve workload balance.

#### storage

* database
  * redis
  * postgres sql
* storage
  * azure blob

#### resource management and task dispatch

* Controller node maintains a sequence of available instances nodes and performs heartbeat checks on these nodes at regular intervals

```
node_info:{
  machineName: "A",
  location: "Nanjing",
  networkType: "wired",
  publicIP: true,
  IP_address: "120.23.23.4",
  avaliable_ports: ["5000-10000"],
  expired_time: "----/--/--"
}
```

* Task is dispatched according to the experiment config file.

```
lab_resourceRequest:{
  labID: 1,
  vm_num: 3,
  vm_config: [
    {networkType:"wired", portNum: 1},
    {networkType:"wired", portNum: 1},
    {networkType:"wired", portNum: 1}
  ]
}
```

### experiment running code

## IMPLEMENTATION

### OpenNetLab framework

the expected structure of OpenNetLab package

```
|-- Protocol
  |-- onl_packet.py
  |-- ...
|-- Logger
|-- Evaluator
|-- Utils
|-- Nodes
  |-- client_node.py
  |-- server_node.py
  |-- p2p_node.py
  |-- ...
```

### design a new lab

design the **experiment-specific server node** using ONL framework.

```python
from OpenNetLab import ServerNode
class MyOwnServerNode(ServerNode):
    # override the callback when receiving packet from client
    def recv_callback(self, data):
	pass
```

design the **experiment-specific client node** using ONL framework.

```python
from OpenNetLab import ClientNode
class MyOwnClientNode(ClientNode):
    # override the handler to process test case and send packets to server
    def testcase_handler(self, data):
	pass
```

lab design directory structure

```
| -- node
  | -- MyServer.py
  | -- MyClient.py
| -- other lab modules
| -- requirements.txt
| -- README.md
| -- config.yml
```

configure the experiment in `config.yml` file

```
node:
  node_type: cs
  node_num: 2
  server_node: node/MyServer.py
  client_node: node/MyClient.py
  ...
```

## TIME SCHEDULE

* 3.17 ~ 3.31

- [x] work plan
- [x] protocol implementation in ONL package

* 4.1 ~ 4.14


* 4.15 ~ 4.28
