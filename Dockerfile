FROM python:3.9-slim as base

FROM base as builder

RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN apt-get update

# Some packages don't have wheels on armv7 so extra packages are required to get it to compile
RUN apt-get install lsb-release gcc libc-dev -y --no-install-recommends
RUN apt-get install libffi-dev -y --no-install-recommends
RUN pip install --prefix=/install -r /requirements.txt

FROM base

COPY --from=builder /install /usr/local
COPY ./ /app
RUN pip install -e /app
WORKDIR /app
CMD ["python3", "-m", "metasorter.main", "-c", "/app/config.json"]