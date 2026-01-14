"""
Resource Loader - Centralized loading and parsing of casos.md and politicas.md

This module replaces the scattered logic for loading resources across multiple files.
It provides a clean, singleton-based interface for accessing policies and cases.
"""
import logging
from typing import Dict, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ResourceLoader:
    """
    Centralized loader for policies (politicas.md) and cases (casos.md).

    This class:
    - Loads markdown files once at initialization
    - Parses them into structured sections
    - Provides clean access methods
    - Singleton pattern for efficiency
    """

    def __init__(self, base_path: str = None):
        """
        Initialize the resource loader.

        Args:
            base_path: Base directory path (defaults to project root)
        """
        if base_path is None:
            # Auto-detect project root (3 levels up from this file)
            current_file = Path(__file__)
            base_path = str(current_file.parent.parent.parent.parent)

        self.base_path = Path(base_path)
        self.politicas = self._load_politicas()
        self.casos = self._load_casos()

        logger.info(f"ResourceLoader initialized: {len(self.politicas)} policies, {len(self.casos)} cases")

    def _load_politicas(self) -> Dict[str, str]:
        """
        Load and parse politicas.md into sections.

        Returns:
            Dict mapping policy title to policy content
        """
        politicas_path = self.base_path / "politicas.md"

        if not politicas_path.exists():
            logger.warning(f"politicas.md not found at {politicas_path}")
            return {}

        with open(politicas_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse into sections by numbered headers (e.g., "1. Title", "2. Title")
        politicas = {}
        current_section = None
        current_content = []

        for line in content.split('\n'):
            stripped = line.strip()

            # Detect section headers: "1. Title" or "• Item"
            if stripped and (stripped[0].isdigit() or stripped.startswith('•')):
                # Save previous section
                if current_section:
                    politicas[current_section] = '\n'.join(current_content).strip()

                # Start new section
                current_section = stripped
                current_content = [line]
            elif current_section:
                current_content.append(line)

        # Save last section
        if current_section:
            politicas[current_section] = '\n'.join(current_content).strip()

        logger.info(f"Loaded {len(politicas)} policy sections")
        return politicas

    def _load_casos(self) -> Dict[str, str]:
        """
        Load and parse casos.md into categories.

        Returns:
            Dict mapping case category to case content
        """
        casos_path = self.base_path / "casos.md"

        if not casos_path.exists():
            logger.warning(f"casos.md not found at {casos_path}")
            return {}

        with open(casos_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Parse into categories by numbered headers
        casos = {}
        current_category = None
        current_content = []

        for line in content.split('\n'):
            stripped = line.strip()

            # Detect category headers: "1. Title" (not indented)
            if stripped and stripped[0].isdigit() and '.' in stripped and not line.startswith('  '):
                # Save previous category
                if current_category:
                    casos[current_category] = '\n'.join(current_content).strip()

                # Start new category
                current_category = stripped
                current_content = [line]
            elif current_category:
                current_content.append(line)

        # Save last category
        if current_category:
            casos[current_category] = '\n'.join(current_content).strip()

        logger.info(f"Loaded {len(casos)} case categories")
        return casos

    def get_all_politicas(self) -> Dict[str, str]:
        """Get all policies as dict."""
        return self.politicas.copy()

    def get_all_casos(self) -> Dict[str, str]:
        """Get all cases as dict."""
        return self.casos.copy()

    def get_politicas_list(self) -> List[str]:
        """Get all policies as a list of strings."""
        return list(self.politicas.values())

    def get_casos_list(self) -> List[str]:
        """Get all cases as a list of strings."""
        return list(self.casos.values())

    def get_politica_by_title(self, title: str) -> str:
        """
        Get a specific policy by its title.

        Args:
            title: Policy title (exact or partial match)

        Returns:
            Policy content or empty string if not found
        """
        # Exact match
        if title in self.politicas:
            return self.politicas[title]

        # Partial match
        for key, value in self.politicas.items():
            if title.lower() in key.lower():
                return value

        logger.warning(f"Policy not found: {title}")
        return ""

    def get_caso_by_title(self, title: str) -> str:
        """
        Get a specific case by its title.

        Args:
            title: Case title (exact or partial match)

        Returns:
            Case content or empty string if not found
        """
        # Exact match
        if title in self.casos:
            return self.casos[title]

        # Partial match
        for key, value in self.casos.items():
            if title.lower() in key.lower():
                return value

        logger.warning(f"Case not found: {title}")
        return ""


# Singleton instance
_resource_loader_instance = None


def get_resource_loader() -> ResourceLoader:
    """
    Get the singleton ResourceLoader instance.

    Returns:
        ResourceLoader instance
    """
    global _resource_loader_instance
    if _resource_loader_instance is None:
        _resource_loader_instance = ResourceLoader()
    return _resource_loader_instance
