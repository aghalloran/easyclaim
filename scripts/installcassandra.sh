#!/bin/bash

# 1. Create & mount EBS volume to /mnt/cassandra
# 2. Run this script

mkdir /opt/apache-cassandra-1.0.9
wget -P /tmp http://mirrors.gigenet.com/apache/cassandra/1.0.9/apache-cassandra-1.0.9-bin.tar.gz
sudo tar -xzvf /tmp/apache-cassandra-1.0.9-bin.tar.gz -C /opt/
mkdir -p /mnt/cassandra/data
mkdir -p /mnt/cassandra/commitlog
mkdir -p /mnt/cassandra/saved_caches
chown -R ec2-user.ec2-user /mnt/cassandra
mkdir -p /var/log/cassandra
chown -R ec2-user.ec2-user /var/log/cassandra
cp ../config/cassandra/cassandra.yaml /opt/apache-cassandra-1.0.0/conf

