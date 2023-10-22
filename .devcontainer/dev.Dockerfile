From python:3.12

WORKDIR /gitlabform

COPY ../ .

RUN python setup.py develop && \
  pip install -e '.[test]'
