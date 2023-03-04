# CalderaAgent-Docker
Docker container of a simple agent for MITRE Caldera written in python 

Useful commands for container image:

1)To build: `docker build -t containertag .`    
2)To remove: `docker image rm containertag -f`  
3)To run without caring for `docker run -i --net=host -t containertag`     
**--net=host** option is used to make the programs inside the Docker container look like they are running on the host itself, from the perspective of the network


