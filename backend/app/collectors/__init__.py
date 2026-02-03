from importlib import import_module

__all__ = ["BaseCollector", "RawArticle", "CollectorManager"]


def __getattr__(name: str):
    if name in {"BaseCollector", "RawArticle"}:
        mod = import_module("app.collectors.base")
        return getattr(mod, name)
    if name == "CollectorManager":
        mod = import_module("app.collectors.manager")
        return getattr(mod, name)
    raise AttributeError(name)
