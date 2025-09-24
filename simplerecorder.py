from simple_recorder.utils.logging_config import configure_logging
from simple_recorder.ui.app import SimpleRecorderApp


def main() -> None:
    configure_logging()
    app = SimpleRecorderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
