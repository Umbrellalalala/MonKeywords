# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25 11:26
@Auth: Zhang Hongxing
@File: flushall.py
@Note:   
"""
# -*- coding: utf-8 -*-
"""
@Time: 2024/12/25
@Auth: Zhang Hongxing
@File: clear_cache.py
@Note: 清空当前 Redis 集群的所有键值对
"""
from redis_config import get_redis_cluster_client

redis_client = get_redis_cluster_client()


def clear_all_cache():
    """
    清空 Redis 集群中的所有键值对
    """
    try:
        redis_client.flushall()
        print("Redis 集群中的所有键值对已清空。")
    except Exception as e:
        print(f"清空缓存时发生错误: {e}")


if __name__ == "__main__":
    clear_all_cache()
