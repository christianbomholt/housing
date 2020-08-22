#! /bin/bash

export FLASK_APP=app/

flask scrape
flask process


FILE=hist_data.csv
if [[ ! -f "$FILE" ]]; then
    echo "$FILE not found."
    flask scrape_hist
fi

flask init-db
flask run -h 0.0.0.0 --port=5001
