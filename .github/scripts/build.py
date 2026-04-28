"""Build script for marimo notebooks with BIDS dataset support.

This script exports marimo notebooks to HTML/WebAssembly format and generates
an index.html file. It handles copying the BIDS dataset for browser access.
"""

# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "jinja2==3.1.3",
#     "fire==0.7.0",
#     "loguru==0.7.0"
# ]
# ///

import shutil
import subprocess
from pathlib import Path
from typing import List, Union

import fire
import jinja2
from loguru import logger


def _export_html_wasm(
    notebook_path: Path, output_dir: Path, as_app: bool = False
) -> bool:
    """Export a single marimo notebook to HTML/WebAssembly format."""
    output_path: Path = notebook_path.with_suffix(".html")

    # Base command for marimo export
    cmd: List[str] = ["uvx", "marimo@0.16.2", "export", "html-wasm", "--sandbox"]

    if as_app:
        logger.info(f"Exporting {notebook_path} to {output_path} as app")
        cmd.extend(["--mode", "run", "--show-code"])
    else:
        logger.info(f"Exporting {notebook_path} to {output_path} as notebook")
        cmd.extend(["--mode", "edit"])

    try:
        output_file: Path = output_dir / notebook_path.with_suffix(".html")
        output_file.parent.mkdir(parents=True, exist_ok=True)

        cmd.extend([str(notebook_path), "-o", str(output_file)])

        logger.debug(f"Running command: {cmd}")
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        logger.info(f"Successfully exported {notebook_path}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error exporting {notebook_path}:")
        logger.error(f"Command output: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error exporting {notebook_path}: {e}")
        return False


def _generate_index(
    output_dir: Path,
    template_file: Path,
    notebooks_data: List[dict] | None = None,
    apps_data: List[dict] | None = None,
) -> None:
    """Generate an index.html file that lists all the notebooks."""
    logger.info("Generating index.html")

    index_path: Path = output_dir / "index.html"
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        template_dir = template_file.parent
        template_name = template_file.name
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=jinja2.select_autoescape(["html", "xml"]),
        )
        template = env.get_template(template_name)

        rendered_html = template.render(notebooks=notebooks_data, apps=apps_data)

        with open(index_path, "w") as f:
            f.write(rendered_html)
        logger.info(f"Successfully generated index.html at {index_path}")

    except IOError as e:
        logger.error(f"Error generating index.html: {e}")
    except jinja2.exceptions.TemplateError as e:
        logger.error(f"Error rendering template: {e}")


def _export(folder: Path, output_dir: Path, as_app: bool = False) -> List[dict]:
    """Export all marimo notebooks in a folder to HTML/WebAssembly format."""
    if not folder.exists():
        logger.warning(f"Directory not found: {folder}")
        return []

    notebooks = list(folder.rglob("*.py"))
    logger.debug(f"Found {len(notebooks)} Python files in {folder}")

    if not notebooks:
        logger.warning(f"No notebooks found in {folder}!")
        return []

    notebook_data = [
        {
            "display_name": (nb.stem.replace("_", " ").title()),
            "html_path": str(nb.with_suffix(".html")),
        }
        for nb in notebooks
        if _export_html_wasm(nb, output_dir, as_app=as_app)
    ]

    logger.info(
        f"Successfully exported {len(notebook_data)} out of {len(notebooks)} files from {folder}"
    )
    return notebook_data


def _copy_dataset(output_dir: Path) -> None:
    """Copy BIDS dataset to output directory for browser access."""
    dataset_src = Path("datasets/bids-examples/ds114")
    dataset_dst = output_dir / "data" / "ds114"

    if not dataset_src.exists():
        logger.warning(f"Dataset not found at {dataset_src}")
        return

    logger.info(f"Copying dataset from {dataset_src} to {dataset_dst}")
    dataset_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(dataset_src, dataset_dst, dirs_exist_ok=True)
    logger.info("Dataset copied successfully")


def main(
    output_dir: Union[str, Path] = "_site",
    template: Union[str, Path] = "templates/index.html.j2",
) -> None:
    """Main function to export marimo notebooks."""
    logger.info("Starting marimo build process")

    output_dir_path: Path = Path(output_dir)
    logger.info(f"Output directory: {output_dir_path}")

    output_dir_path.mkdir(parents=True, exist_ok=True)

    template_file: Path = Path(template)
    logger.info(f"Using template file: {template_file}")

    # Export notebooks from the notebooks/ directory
    notebooks_data = _export(Path("notebooks"), output_dir_path, as_app=False)

    # Export apps from the examples/ directory (migration guide as app)
    apps_data = _export(Path("examples"), output_dir_path, as_app=True)

    if not notebooks_data and not apps_data:
        logger.warning("No notebooks or apps found!")
        return

    # Copy BIDS dataset for browser access
    _copy_dataset(output_dir_path)

    # Generate the index.html file
    _generate_index(
        output_dir=output_dir_path,
        notebooks_data=notebooks_data,
        apps_data=apps_data,
        template_file=template_file,
    )

    logger.info(f"Build completed successfully. Output directory: {output_dir_path}")


if __name__ == "__main__":
    fire.Fire(main)
