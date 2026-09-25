from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version

from ocelescope_module_socel.ocean.api import router as ocean
from ocelescope_module_socel.ocean.api.exception_handlers import (
    register_exception_handlers as register_ocean_exception_handlers,
)


class Socel(Module):
    # Mounted at /modules/socel/v1; each page's API has its own prefix below
    # that, e.g. /ocean. The frontend's `generate:api` script uses this key.
    meta = ModuleMeta(key="socel", version=Version("1.0"))

    @classmethod
    def create_app(cls) -> FastAPI:
        app = FastAPI(title="sOCEL", version=str(cls.meta.version), docs_url=None, redoc_url=None)
        register_ocean_exception_handlers(app)
        app.include_router(ocean.router)
        return app
