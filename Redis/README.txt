./config_cluster/: 用于搭建分片集群的配置文件
./config_sentinel/: 用于搭建哨兵节点的配置文件
1. 请将此文件夹内的所有文件原封不动地移动至D:/redis/下
2. 运行D:/redis/redis-server.exe
3. 在cmd中输入ipconfig，然后将每一个conf文件中的ip地址替换为自己的ip地址
执行以下命令
4. 搭建分片集群
    1. 启动容器
    docker run -id --name redis_6380 -p 6380:6380 -p 16380:16380 --privileged=true -v /d/redis/conf_cluster/data/6380:/data -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6380.conf
    docker run -id --name redis_6381 -p 6381:6381 -p 16381:16381 --privileged=true -v /d/redis/conf_cluster/data/6381:/data -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6381.conf
    docker run -id --name redis_6382 -p 6382:6382 -p 16382:16382 --privileged=true -v /d/redis/conf_cluster/data/6382:/data -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6382.conf
    docker run -id --name redis_6390 -p 6390:6390 -p 16390:16390 --privileged=true -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6390.conf
    docker run -id --name redis_6391 -p 6391:6391 -p 16391:16391 --privileged=true -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6391.conf
    docker run -id --name redis_6392 -p 6392:6392 -p 16392:16392 --privileged=true -v /d/redis/conf_cluster:/etc/redis redis redis-server /etc/redis/redis-6392.conf
    2. 查看各节点ip
    docker inspect redis_6380
    docker inspect redis_6381
    docker inspect redis_6382
    docker inspect redis_6390
    docker inspect redis_6391
    docker inspect redis_6392
    3. 创建集群
    docker exec -it redis_6380 /bin/bash
    redis-cli --cluster create 172.17.0.2:6380 172.17.0.5:6390 172.17.0.3:6381 172.17.0.6:6391 172.17.0.4:6382 172.17.0.7:6392 --cluster-replicas 1
    4. 查看集群信息
    redis-cli -p 6380 cluster nodes
5. 搭建哨兵节点
    1. 启动容器
    docker run -d --name redis_sentinel1 -p 26380:26380 --privileged=true -v /d/redis/conf_sentinel:/etc/redis redis redis-server /etc/redis/redis-26380.conf --sentinel
    docker run -d --name redis_sentinel2 -p 26381:26381 --privileged=true -v /d/redis/conf_sentinel:/etc/redis redis redis-server /etc/redis/redis-26381.conf --sentinel
    docker run -d --name redis_sentinel3 -p 26382:26382 --privileged=true -v /d/redis/conf_sentinel:/etc/redis redis redis-server /etc/redis/redis-26382.conf --sentinel
    2. 查看哨兵信息
    docker exec -it redis_sentinel1 /bin/bash
    redis-cli -p 26380 sentinel masters
    3. 检查哨兵是否正常工作
    docker exec -it redis_sentinel1 redis-cli -p 26380 info sentinel
    docker exec -it redis_sentinel2 redis-cli -p 26381 info sentinel
    docker exec -it redis_sentinel3 redis-cli -p 26382 info sentinel