from app import create_app
from waitress import serve
import logging
import os
import warnings

app = create_app()

# Template/static reloading — only meaningful in debug
_debug = os.environ.get("FLASK_DEBUG") == "1"
app.config["TEMPLATES_AUTO_RELOAD"] = _debug
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0 if _debug else None
app.jinja_env.auto_reload = _debug

if __name__ == "__main__":
    port = int(os.environ.get("FLASK_PORT", 5000))

    if _debug:
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        # Silence warnings in production — they were already printed at import time
        warnings.filterwarnings("ignore", category=UserWarning, module="config")
        logging.getLogger("waitress").setLevel(logging.INFO)
        serve(app, host="0.0.0.0", port=port, threads=4)