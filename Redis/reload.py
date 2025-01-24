from Mysql.db_config import DB_PARAMS
from Redis.redis_config import get_redis_cluster_client
from src.data_storage.database import Database
from src.data_storage.models import Summary
from apscheduler.schedulers.background import BackgroundScheduler
import time


class CacheManager:
    def __init__(self):
        self.db = Database(DB_PARAMS)
        self.redis_client = get_redis_cluster_client()
        self.scheduler = BackgroundScheduler()

    def query_database(self, model, key):
        session = self.db.get_session()
        try:
            result = session.query(model).filter_by(id=key).first()
            return result
        finally:
            session.close()

    def get_hot_keys(self):
        # 返回所有摘要的 ID
        return [summary.id for summary in self.db.get_session().query(Summary).all()]

    def reload_cache(self, model):
        hot_keys = self.get_hot_keys()
        for key in hot_keys:
            print(f"Reloading cache for key: {key}")
            value = self.query_database(model, key)
            if value:
                self.redis_client.set(key, value, ex=3600)
                print(f"Cache reloaded for key: {key}")
            else:
                print(f"No data found for key: {key}")

    def schedule_cache_reloading(self, model, interval_seconds=3600):
        self.scheduler.add_job(lambda: self.reload_cache(model), 'interval', seconds=interval_seconds)
        self.scheduler.start()

    def start(self, model):
        self.reload_cache(model)  # 初始化时刷新缓存
        self.schedule_cache_reloading(model)  # 启动定时任务

    def stop(self):
        self.scheduler.shutdown()


if __name__ == "__main__":
    cache_manager = CacheManager()
    try:
        cache_manager.start(Summary)
        while True:
            time.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        print("Shutting down...")
        cache_manager.stop()
