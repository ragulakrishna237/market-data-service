from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    port: int = 8000
    tick_interval_min: float = 0.1
    tick_interval_max: float = 1.0
    heartbeat_interval_s: float = 2.0
    
    # Fault injection flags (M2)
    fault_gap_every_n: int = 0
    fault_bad_tick_rate: float = 0.0
    fault_stale_ts_rate: float = 0.0
    fault_disconnect_after_s: int = 0
    fault_stall_after_s: int = 0

    class Config:
        env_file = ".env"

config = Settings()
