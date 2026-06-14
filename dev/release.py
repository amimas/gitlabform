"""Tasks related to releasing artifacts (PyPI and Docker)."""

import argparse
from dev.common import run_command, get_executable


def publish_pypi(extra_args: list[str] | None = None):
    """Publishes the built Python artifacts to PyPI.

    Args:
        extra_args: Additional arguments for uv publish.
    """
    run_command(["uv", "publish"] + (extra_args or []), "Publishing package to PyPI")


def publish_docker(extra_args: list[str] | None = None):
    """Pushes the built Docker image to a registry.

    Args:
        extra_args: Arguments for the docker push command (e.g., --image, --tag).
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--image", default="localhost/gitlabform")
    parser.add_argument("--tag", default="latest")

    parsed, remaining = parser.parse_known_args(extra_args or [])
    image_name = f"{parsed.image}:{parsed.tag}"
    docker_bin = get_executable("docker")

    run_command([docker_bin, "push", image_name], f"Pushing Docker image: [bold cyan]{image_name}[/bold cyan]")
