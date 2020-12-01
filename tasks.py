"""
Configure the invoke release task
"""

from invoke_release.plugins import PatternReplaceVersionInFilesPlugin
from invoke_release.tasks import *  # noqa: F403

configure_release_parameters(  # noqa: F405
    module_name="gitlab_api",
    display_name="gitlab-api",
    # python_directory="package",
    plugins=[
        PatternReplaceVersionInFilesPlugin(
            "docs/conf.py", "gitlab_api/version.py", "pyproject.toml", "README.md"
        )
    ],
)
