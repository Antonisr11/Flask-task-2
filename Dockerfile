FROM ubuntu:16.04
RUN apt-get update #&& apt-get install -y
RUN apt-get install -y python3
RUN apt-get install -y python3-pip
RUN pip3 install requests
RUN mkdir /script
COPY main.py /script
CMD ["python3","-u", "/script/main.py"]