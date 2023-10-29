From python:3.12

COPY ../README.md ../version ../setup.py /gitlabform-deps/

RUN cd /gitlabform-deps && \
  python setup.py develop && \
  pip install -e '.[test]'
