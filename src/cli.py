"""Command-line interface for roadmap scraper."""

import logging
import sys
from typing import Optional
import click
from .json_scraper import JSONRoadmapScraper
from .github_fetcher import GitHubFetcher


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the application.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@click.group()
def cli() -> None:
    """Roadmap.sh scraper - Extract roadmap data to CSV."""
    pass


@cli.command()
@click.option(
    "--roadmap",
    default=None,
    help="Roadmap name (e.g., engineering-manager, frontend, backend)",
)
@click.option(
    "--output",
    type=click.Path(),
    default=None,
    help="Output CSV path (default: auto-generated with timestamp)",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    default=False,
    help="Show interactive roadmap selection menu",
)
@click.option(
    "--list",
    "list_roadmaps",
    is_flag=True,
    default=False,
    help="List all available roadmaps and exit",
)
@click.option(
    "--verbose", "-v", is_flag=True, default=False, help="Enable verbose logging"
)
@click.option(
    "--enrich",
    is_flag=True,
    default=False,
    help="Enrich CSV with AI-generated summaries (TLDR, Challenge)",
)
@click.option(
    "--gemini-api-key",
    envvar="GEMINI_API_KEY",
    default=None,
    help="Google Gemini API key (or set GEMINI_API_KEY env var)",
)
def scrape(
    roadmap: Optional[str],
    output: Optional[str],
    interactive: bool,
    list_roadmaps: bool,
    verbose: bool,
    enrich: bool,
    gemini_api_key: Optional[str],
) -> None:
    """Scrape a roadmap from GitHub and export to CSV.

    This tool fetches roadmap data directly from the roadmap.sh GitHub repository,
    parses the JSON structure and content files, and exports to CSV format.

    Examples:

        # Basic usage (engineering-manager roadmap)
        python -m src.cli scrape

        # Different roadmap
        python -m src.cli scrape --roadmap frontend

        # Custom output path
        python -m src.cli scrape --output my_roadmap.csv

        # Verbose mode to see detailed progress
        python -m src.cli scrape -v
    """
    setup_logging(verbose)

    try:
        # Validate enrichment flags
        if enrich and not gemini_api_key:
            click.secho(
                "Error: --gemini-api-key required when using --enrich", fg="red"
            )
            click.echo(
                "Provide via --gemini-api-key flag or GEMINI_API_KEY environment variable"
            )
            sys.exit(1)

        # Handle --list flag: show all roadmaps and exit
        if list_roadmaps:
            click.echo("🗺️  Fetching available roadmaps from GitHub...")
            fetcher = GitHubFetcher()
            roadmaps = fetcher.list_available_roadmaps()

            click.echo(f"\nAvailable Roadmaps ({len(roadmaps)} found):\n")
            for name in roadmaps:
                click.echo(f"  - {name}")
            click.echo()
            sys.exit(0)

        # Handle --interactive flag: show selection menu
        if interactive:
            click.echo("🗺️  Scanning available roadmaps from GitHub...\n")
            fetcher = GitHubFetcher()
            roadmaps = fetcher.list_available_roadmaps()

            click.echo(f"Available Roadmaps ({len(roadmaps)} found):\n")

            # Display numbered list in columns
            for i, name in enumerate(roadmaps, 1):
                click.echo(f"  {i:3d}. {name}")

            click.echo()

            # Prompt for selection
            while True:
                selection = click.prompt("Select roadmap (number or name)", type=str)

                # Try as number first
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(roadmaps):
                        roadmap = roadmaps[idx]
                        break
                    else:
                        click.secho(
                            f"Invalid number. Please enter 1-{len(roadmaps)}",
                            fg="yellow",
                        )
                        continue

                # Try as name
                if selection in roadmaps:
                    roadmap = selection
                    break
                else:
                    click.secho(
                        f"Roadmap '{selection}' not found. Please try again.",
                        fg="yellow",
                    )
                    continue

            click.secho(f"\n✓ Selected: {roadmap}\n", fg="green", bold=True)

        # Ensure we have a roadmap name
        if not roadmap:
            click.secho(
                "Error: Please specify a roadmap using --roadmap or --interactive",
                fg="red",
            )
            click.echo("Use --list to see available roadmaps")
            sys.exit(1)

        scraper = JSONRoadmapScraper(roadmap_name=roadmap, output_path=output)

        csv_path = scraper.scrape(enrich=enrich, gemini_api_key=gemini_api_key)

        click.echo()
        click.secho("✓ Scraping completed successfully!", fg="green", bold=True)
        click.echo(f"Output file: {csv_path}")

        sys.exit(0)

    except KeyboardInterrupt:
        click.echo()
        click.secho("✗ Scraping interrupted by user", fg="yellow")
        sys.exit(1)

    except Exception as e:
        click.echo()
        click.secho(f"✗ Scraping failed: {e}", fg="red", bold=True)
        if verbose:
            import traceback

            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
