FROM python:2.7-slim
RUN apt-get update && apt-get install -yq netcat && apt-get clean

WORKDIR /redisproxy

ADD requirements.txt /redisproxy/requirements.txt
RUN pip install -r requirements.txt

ADD threaded_proxy.py /redisproxy/threaded_proxy.py
ADD test_redis_data.py /redisproxy/test_redis_data.py

CMD ["python", "/redisproxy/test_redis_data.py"]
CMD ["python", "/redisproxy/threaded_proxy.py", "--addr=redis"]
