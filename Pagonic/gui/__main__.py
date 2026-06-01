"""Entry point for the optional Pagonic GUI."""


def main() -> None:
    """Launch the GUI or show a clear dependency message."""
    try:
        from Pagonic.gui.windows.main_window import main as run_gui
    except ModuleNotFoundError as exc:
        if exc.name == "PyQt6":
            raise SystemExit(
                "Pagonic GUI requires PyQt6. Install it with 'pip install pagonic[gui]'."
            ) from exc
        raise

    run_gui()


if __name__ == "__main__":
    main()
