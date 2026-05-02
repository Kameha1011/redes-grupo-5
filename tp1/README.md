# File Transfer UDP

## Requirements

- Python 3.12 or higher.
- GNU/Linux Operating system (Maybe could work in others but we only give to support to GNU/Linux).

## Environment Setup

1. Create a virtual environment with `venv`.

`python3 -m venv .venv`

2. Activate it.

`source .venv/bin/activate`

## How to run

-  Start the server on your terminal like this:

`python3 src/start-server.py -H 0.0.0.0 -p 9000 -s ./server_storage`

- Now open other terminal and you can start uploading/downloading files like this:

`python3 src/upload.py -H 127.0.0.1 -p 9000 -s ~/Documents -n file.pdf -r stop_and_wait`

`python3 src/download.py -H 127.0.0.1 -p 9000 -d ~/Documents -n file.pdf -r stop_and_wait`


## Wireshark packet monitoring

We created a Wireshark plugin to filter out all packets coming from this project, to monitor packets run on your terminal:

`wireshark -i lo -X  lua_script:plugin-wireshark/protocol.lua`

Then on wireshark filters type `protocologrupo5` and it should filter the packets. 


## MININET

# Limpiar cualquier estado previo de Mininet
sudo mn -c

# Ejecutar la topologia de mininet -> abre 2 terminales, la primera es el server y la segunda el client.
sudo python3 topology-mininet/topology.py

# Capturar con wireshark
wireshark -i s1-eth1 -X lua_script:plugin-wireshark/protocol.lua

# En la terminal server ejecutar
python3 src/start-server.py -H 10.0.0.1 -p 9000 -s ./server_storage

# En la terminal cliente ejecutar
python3 src/upload.py -H 10.0.0.1 -p 9000 -s ~/Documents -n file.pdf -r stop_and_wait
python3 src/download.py -H 10.0.0.1 -p 9000 -d ~/Documents -n file.pdf -r stop_and_wait

### Verificación de Integridad
Debido al 10% de pérdida de paquetes, notarás reintentos en las terminales. Al finalizar, verifica que el archivo no se haya corrompido comparando los hashes MD5 en ambas máquinas:

# En la terminal server
md5sum ./server_storage/file.pdf

# En la terminal client
md5sum ~/Documents/file.pdf



## Examples

