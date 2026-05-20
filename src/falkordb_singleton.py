from falkordb import FalkorDB  # type: ignore
from config.config_settings import ConfigSettings

class FalkorDBSingleton:
    _instance = None
    _db = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FalkorDBSingleton, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._db is None:
            settings = ConfigSettings()
            self._db = FalkorDB(host=settings.falkordb_config.falkor_host, port=settings.falkordb_config.falkor_port)
    
    def get_db(self):
        return self._db