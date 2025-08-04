import logging
from gui import create_gui

def setup_logging():
    """Configures logging to save errors to a file."""
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='error.log',
        filemode='a'
    )

def main():
    """
    The main entry point of the application.
    """
    setup_logging()
    create_gui()

if __name__ == "__main__":
    main()