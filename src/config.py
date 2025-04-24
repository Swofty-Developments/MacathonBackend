from __future__ import annotations

# See https://docs.python.org/3/faq/programming.html#how-do-i-share-global-variables-across-modules

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI

    from models.config_models import AppConfigDto


INTERFACE_API_KEY: str = os.getenv("INTERFACE_API_KEY")

app: FastAPI = None
app_config: AppConfigDto = None
# TODO: Add MongoDB connection type hint below.
db  = None
