from __future__ import annotations

# See https://docs.python.org/3/faq/programming.html#how-do-i-share-global-variables-across-modules

import os
from typing import TYPE_CHECKING

from modules.db import MongoClient

if TYPE_CHECKING:
    from fastapi import FastAPI

    from models.config_models import AppConfigDto


app: FastAPI = None
app_config: AppConfigDto = None
# TODO: Add MongoDB connection type hint below.
db: MongoClient = None
