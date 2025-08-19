import os
from pydantic import SecretStr
from pydantic_settings import BaseSettings
from pydantic_settings import SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), ".envs/.env"))
    TELEGRAM_API_KEY: SecretStr = SecretStr("secret")
    LOG_LEVEL: str = "INFO"

class ConnectorSettings(BaseSettings):
    host: str = 'localhost'
    database: str = ''
    username: str = ''
    password: str = ''

    model_config = SettingsConfigDict(env_file=os.path.join(os.path.dirname(__file__), ".envs/.envdb"))

settings = ConnectorSettings()


# print(settings.model_config)
# print(settings.host)
# print(settings.database)
# print(settings.username)
# print(settings.password)