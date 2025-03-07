# from fastapi import FastAPI, UploadFile, Request, Response

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Response

from fastapi.staticfiles import StaticFiles
from astropy.io import fits
import numpy as np
import logging
import os
from io import BytesIO
import matplotlib.pyplot as plt
from gdrive import authenticate_drive, get_flow
from astropy.io import fits
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.widgets import Button

from fastapi.responses import HTMLResponse
import matplotlib.pyplot as plt
import numpy as np
import os
from astropy.io import fits
from io import BytesIO
import base64
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse
import matplotlib.pyplot as plt
import numpy as np
import os
from astropy.io import fits
from io import BytesIO

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("static/index.html", "r") as f:
        return f.read()
        
@app.get("/login")
async def login():
    flow = get_flow()
    auth_url, _ = flow.authorization_url(prompt='consent')
    return RedirectResponse(auth_url)
    
    
CACHE_DIR = "/data/cache"
os.makedirs(CACHE_DIR, exist_ok=True)


@app.get("/view-fits/")
async def view_fits():
    try:
        cached_file = os.path.join(CACHE_DIR, "ngc0628_miri_lv3_f2100w_i2d_anchor.fits")

        if not os.path.exists(cached_file):
            return {"error": "FITS file not found in cache"}

        # Open FITS file and extract data
        with fits.open(cached_file) as hdul:
            image_data = hdul[1].data.astype(float)

        # Convert NaN values to zero
        image_data = np.nan_to_num(image_data)

        # Create Matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 10))  # Larger image for better zooming
        im = ax.imshow(image_data, cmap="gray", origin="lower")
        plt.axis("off")  # Hide axes for better viewing

        # Save image as high-resolution PNG
        image_path = os.path.join(CACHE_DIR, "fits_image.png")
        plt.savefig(image_path, format="png", bbox_inches="tight", dpi=300)

        return FileResponse(image_path, media_type="image/png")

    except Exception as e:
        return {"error": f"Failed to display FITS file: {str(e)}"}
        
@app.get("/oauth2callback")
async def oauth2callback(request: Request):
    try:
        flow = get_flow()
        flow.fetch_token(authorization_response=str(request.url))

        creds = flow.credentials

        # Ensure Railway's /data directory exists
        os.makedirs("/data", exist_ok=True)

        # Save token securely in Railway's /data storage
        with open("/data/token.json", "w") as token_file:
            token_file.write(creds.to_json())

        return {"message": "Authentication successful! You can now access Google Drive files."}

    except Exception as e:
        return {"error": f"Failed to authenticate: {str(e)}"}
