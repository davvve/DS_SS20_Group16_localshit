# Local's Hit

![Logo_LocalsHit](logo_localshit.png)

Project of Lecture DBE14 Distributed Systems

## Team Members

- Markus Drespling
- Frederick Dehner
- David Lüttmann

## Install & run
Install:

1. Update pip: ```pip install --upgrade pip```
2. Update setuptools: ```pip install --upgrade setuptools```
3. Install localshit: ```pip install -e .```


Run frontend server:
```
frontend
```

Run backend server(s) with custom frontend server IP:
```
localshit -f "172.17.0.2"
```

Open client:
```
http://[frontend-ip]:8081/index.html
```

Run tests:
```
pytest tests -s
```

# Demo Video
[![Demo-Video](http://img.youtube.com/vi/tH11u04u4Ts/0.jpg)](http://www.youtube.com/watch?v=tH11u04u4Ts "Demo-Video")

## Config
All configuration parameters are stored in `utils/config.py`:
```
config = {
    "frontend_server": "192.168.0.179",
    "ring_multicast_address": "224.1.1.1",
    "ring_multicast_port": 5007,
    "ring_unicast_port": 10001,
    "content_websocket_port": 10013,
    "frontend_unicast_port": 10012,
    "frontend_webserver_port": 8081,
    "reliable_socket": 10033,
    "loglevel": "debug",
    "chuck_norris": True,
    "quote_intervall": 25,
    "announcement_timeout": 1,
    "heartbeat_intervall": 2,
    "heartbeat_timeout": 6,
}
```

# Docker

You can use docker to run multiple servers on one host. If you use multiple servers distributed on more than one host, use Vagrant because Docker doesn't support bridged networks to the local area network.

## Build and run backend

Build Docker image for backends (after every change)

```
docker build -f Dockerfile.backend -t localshit .
```

Run docker

```
docker run --rm localshit
```

## Build and run client

Build Docker image for backends (after every change)

```
docker build -f Dockerfile.client -t localshit-client .
```

Run docker

```
docker run --rm localshit-client
```

## Build and run client

Build Docker image for backends (after every change)

```
docker build -f Dockerfile.frontend -t localshit-frontend .
```

Run docker

```
docker run --rm localshit-frontend
```

## Run tests
```
pytest tests -s
```

# Details about the system

## Message Types

| Type | Parameter 1 | Parameter 2 | Description |
| --- | :--- | :--- | :--- |
| SA | IP address | - | Service announcement - announce backend service to multicast |
| SE | leader candidate IP | isLeader (True/False) | Start election - election messages in the ring |
| HB | heartbeat GUID | - | Heartbeat messages |
| FF | IP address of failed node | - | Failure message when heartbeat fails |
| RP | IP address | - | Reply to sender of service announcement with own IP address |
| LE | IP address of current leader | - | notifies frontend server about current leader |
| CO | content | - | Content messages - send to clients |
| CL | message | - | Notify clients that websocket of backend server is shutting down |
| CR | comment | - | Message type for comments on quotes from the client |
| AA | IP address | - | Send initial message via multicast to get a database update |

# Vagrant

Because Docker doesn't support bridged networking, we choose Vagrant containers with VirtualBox.

## Setup

1. Install VirtualBox
2. Install Vagrant
3. Add hashicorp/bionic64 box image: ``` vagrant box add hashicorp/bionic64```
4. (Init Vagrantfile: ```vagrant init hashicorp/bionic64```)
5. ```vagrant up```
6. ```sudo apt-get updates```
7. ```sudo apt-get -y install python3-pip```
8. Update setuptools: ```pip3 install setuptools```
9. Install localshit: pip3 install -e .
10. sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.6 1
11. Update pip: ```pip install --upgrade pip```
12. Update setuptools: ```pip install --upgrade setuptools```
13. Install localshit: ```pip install -e .```

## Run Vagrant


1. Start vagrant VM: ```vagrant up```
2. Connect to VM via ssh: ```vagrant ssh```
3. Navigate to ```/home/vagrant/code``` and start the server with ```localshit -f "[frontend_ip]"```
4. To stop the VM, use ```vagrant halt```

# Examples
To run the examles within a docker container use

```
docker run -it --rm  -v "$PWD/examples":"/usr/src/widget_app" python:3 python /usr/src/widget_app/dynamicdiscover.py
```
