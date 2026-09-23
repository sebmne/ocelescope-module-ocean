from fastapi import FastAPI
from ocelescope_backend.app.modules import Module, ModuleMeta
from packaging.version import Version

from ocelescope_module_example.routes import router


class Example(Module):
    meta = ModuleMeta(key="example", version=Version("1.0"))

    @classmethod
    def create_app(cls) -> FastAPI:
        app = FastAPI(title="Example", version=str(cls.meta.version))
        app.include_router(router)
        return app
