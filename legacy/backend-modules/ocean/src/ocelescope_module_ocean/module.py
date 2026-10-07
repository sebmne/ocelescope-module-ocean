from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version

from ocelescope_module_ocean.api import router
from ocelescope_module_ocean.api.exception_handlers import register_exception_handlers


class Ocean(Module):
    # Mounted at /modules/ocean/v1. The frontend's `generate:api` script uses this key.
    meta = ModuleMeta(key="ocean", version=Version("1.0"))

    @classmethod
    def create_app(cls) -> FastAPI:
        app = FastAPI(title="OCEAn", version=str(cls.meta.version), docs_url=None, redoc_url=None)
        register_exception_handlers(app)
        app.include_router(router.router)
        return app
