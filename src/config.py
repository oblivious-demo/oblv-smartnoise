from pydantic import BaseSettings, validator, Extra
from typing import Literal, List, Dict, Any
import functools 

import yaml

from models import DPModelSelect

OBLV_CONFIG_PATH = '/usr/runtime.yaml'

def yaml_config(settings: BaseSettings) -> Dict[str, Any]:
    try:
        with open(OBLV_CONFIG_PATH, 'r') as f:
            config_data = yaml.safe_load(f)
    except:
        config_data = {}
    return config_data

class Settings(BaseSettings):
    method: Literal[tuple(DPModelSelect.keys())]
    epsilon:float = 1  # privacy budget
    params:dict = {}  # used to override default params of method
    party_names: List[str]

    @validator('party_names')
    def two_party(cls, v):
        assert len(v) == 2
        return v

    @validator('epsilon')
    def positive_eps(cls, v):
        assert v > 0
        return v

    class Config:
        extra = Extra.allow

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                yaml_config,
                env_settings,
                file_secret_settings,
            )


@functools.lru_cache()
def get_settings() -> Settings:
    return Settings()