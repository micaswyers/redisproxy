FROM python:2.7-slim
RUN apt-get update && apt-get install -yq netcat && apt-get clean

WORKDIR /redisproxy

ADD proxy.py /redisproxy/proxy.py

CMD ["/bin/bash"]
