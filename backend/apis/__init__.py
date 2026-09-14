"""Load legacy routes only when the combined application requests them."""


def __getattr__(name):
    if name == 'all_routers':
        from .toolkitAPI import router as toolkit_router
        from .pypdfAPI import router as pypdf_router
        from .pymupdfAPI import router as pymupdf_router
        return [toolkit_router, pypdf_router, pymupdf_router]
    raise AttributeError(name)
