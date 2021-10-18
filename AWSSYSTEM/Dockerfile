FROM python:3.6-alpine
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN mkdir -p /home/AWSSYSTEM
RUN mkdir -p /home/data
RUN mkdir -p /home/files
RUN mkdir -p /home/data_error
RUN mkdir -p /home/config
RUN mkdir -p /home/timming
RUN mkdir -p /home/log
RUN mkdir -p /home/certification

ADD . /home/AWSSYSTEM

WORKDIR  /home/AWSSYSTEM

EXPOSE 5004

CMD [ "python","__main__.py"]
