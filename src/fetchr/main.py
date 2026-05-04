from .application import FetchrApplication


def main() -> None:
    app = FetchrApplication()
    app.run(None)
