From python:3.12

WORKDIR /gitlabform-docs

COPY ../docs ./docs/
COPY ../.overrides ./.overrides/
COPY ../setup.py .
COPY ../README.md .
COPY ../mkdocs.yml .
COPY ../version .

RUN pip install -e '.[docs]'

EXPOSE 8000

ENTRYPOINT ["mkdocs"]
CMD ["serve", "--no-strict", "--dev-addr=0.0.0.0:8000"]
