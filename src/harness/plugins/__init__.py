"""Plugin registry and built-in plugins."""

from harness.plugins.base import BaseNode

# Global plugin registry
_registry: dict[str, type[BaseNode]] = {}


def register_node(name: str):
    """Decorator to register a plugin node.

    Usage:
        @register_node("my_node")
        class MyNode(BaseNode):
            name = "my_node"
            async def process(self, state, llm):
                ...
    """
    def decorator(cls: type[BaseNode]):
        _registry[name] = cls
        return cls
    return decorator


def get_registered_nodes() -> dict[str, type[BaseNode]]:
    """Return a copy of the current plugin registry."""
    return dict(_registry)


def clear_registry():
    """Clear all registered plugins. Used in testing."""
    _registry.clear()
