"""Load legacy routes only when the combined application requests them."""


def __getattr__(name):
    if name == 'all_routers':
        from .pypdfAPI import router as pypdf_router
        from .pymupdfAPI import router as pymupdf_router
        return [pypdf_router, pymupdf_router]
    raise AttributeError(name)
