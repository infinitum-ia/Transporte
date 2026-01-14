"""
Resources module - Centralized loading of policies and cases
"""
from .resource_loader import ResourceLoader, get_resource_loader

__all__ = ["ResourceLoader", "get_resource_loader"]
