import os
import logging
from logging import FileHandler

basedir = os.path.abspath(os.path.dirname(__file__))

if not os.path.exists("logs"):
    os.makedirs("logs")


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    LOG_LEVEL = logging.INFO
    LOG_FILE = "logs/app.log"
    LOG_FILE_CLIENT = "logs/client.log"


# TODO sistema anche SQLALCHEMY_DATABASE_URI con basedir
class DockerConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "data/database.db")
    NODE_ID = os.environ.get("NODE_ID", None)
    CURRENT_PORT = os.environ.get("PORT", None)


class LocalConfig(Config):
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(basedir, "database.db")
    CURRENT_PORT = 5000
    NODE_ID = 5
    LOG_LEVEL = logging.DEBUG
