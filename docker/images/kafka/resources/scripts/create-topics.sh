#!/bin/bash
#author		 :https://github.com/wurstmeister/kafka-docker
#license	 :https://raw.githubusercontent.com/wurstmeister/kafka-docker/master/LICENSE

if [[ -z "$START_TIMEOUT" ]]; then
    START_TIMEOUT=600
fi

KAFKA_PORT=${KAFKA_PORT:-9092}
KAFKA_SSL_PORT=${KAFKA_SSL_PORT:-9092}
if [ -z "$KAFKA_ZOOKEEPER_CONNECT" ]; then
    KAFKA_ZOOKEEPER_CONNECT=localhost:2181
fi

start_timeout_exceeded=false
count=0
step=5

echo "===> looking for $KAFKA_PORT"
netstat -lnt

while netstat -lnt | awk '$4 ~ /:'$KAFKA_PORT'$/ {exit 1}'; do
    echo "waiting for kafka to be ready"
    sleep $step;
    count=$(expr $count + $step)
    if [ $count -gt $START_TIMEOUT ]; then
        start_timeout_exceeded=true
        break
    fi
done

if $start_timeout_exceeded; then
    echo "Not able to auto-create topic (waited for $START_TIMEOUT sec)"
    exit 1
fi

python3 /parse_and_create_topics.py -i /kafka_topics.json -z $KAFKA_ZOOKEEPER_CONNECT