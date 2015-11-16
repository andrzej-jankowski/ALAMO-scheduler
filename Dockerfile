FROM python:3.5
RUN mkdir /code
WORKDIR /code

ADD alamo_scheduler /code/alamo_scheduler
ADD setup.py /code/
ADD setup.cfg /code/
ADD requirements.txt /code/
ADD contrib /code/contrib
ADD docs /code/docs
ADD .git /code/.git
RUN pip install .

CMD alamo-scheduler -c contrib/docker_config.cfg
