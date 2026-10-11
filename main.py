"""P6 entry point for the Premier League Match Analysis project."""

from scripts.generate_final_report import main as generate_report


def main() -> None:
    """Run the offline P6 processing, visualization, and report workflow."""
    generate_report()


if __name__ == "__main__":
    main()
