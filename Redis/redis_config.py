# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 17:33
@Auth: Zhang Hongxing
@File: redis_config.py
@Note:
"""
from rediscluster import RedisCluster

# 定义集群节点
REDIS_NODES = [
    {"host": "192.168.56.1", "port": 6380},
    {"host": "192.168.56.1", "port": 6381},
    {"host": "192.168.56.1", "port": 6382},
]


def get_redis_cluster_client():
    return RedisCluster(
        startup_nodes=REDIS_NODES,
        decode_responses=True,
    )


if __name__ == "__main__":
    try:
        # 连接 Redis 集群
        redis_client = get_redis_cluster_client()
        print("Redis集群连接成功")
        # 测试获取和设置数据
        cache_key = "a"
        cache_value = "1"
        redis_client.set(cache_key, cache_value)
        print(f"Set key: {cache_key}, value: {cache_value}")
        cached_data = redis_client.get(cache_key)
        print(f"获取到的数据: {cached_data}")
    except Exception as e:
        print(f"Redis集群连接失败: {e}")
