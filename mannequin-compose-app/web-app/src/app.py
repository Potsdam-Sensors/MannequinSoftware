import pandas as pd
import logging
from typing import Union
from web import MannequinApp

logging.basicConfig(level=logging.INFO)

PLACEMENTS_FILE_PATH = "/var/lib/mysql-files/placements.csv"
APP_HOST_ADDR = "0.0.0.0"
APP_PORT = 8888

placements_df: pd.DataFrame = None
app: MannequinApp = None

def setup() -> Union[None, Exception]:
    # Setup sensor placement dataframe
    global placements_df
    try:
        placements_df = pd.read_csv(PLACEMENTS_FILE_PATH)
    except Exception as e:
        return e
    logging.info(f"Placements:\n{placements_df}")

    global app
    try:
        app = MannequinApp(placements_df)
    except Exception as e:
        return e

def main():
    # Setup
    err = setup()
    if err is not None:
        logging.error(f"There was an exception during setup: {err}")
        return
    logging.info("Startup was successful.")

    app.run(debug=True, port=APP_PORT, host=APP_HOST_ADDR)


main()