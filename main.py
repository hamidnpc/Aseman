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
import plotly.graph_objects as go
import plotly.express as px
from bokeh.plotting import figure, output_file, save
from bokeh.resources import CDN
from bokeh.embed import file_html
from bokeh.embed import components
from bokeh.models import ColorBar, LinearColorMapper

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
@app.get("/view-fits/", response_class=HTMLResponse)
async def view_fits():
    try:
        cached_file = os.path.join(CACHE_DIR, "ngc0628_miri_lv3_f2100w_i2d_anchor.fits")

        if not os.path.exists(cached_file):
            service = authenticate_drive()
            folder_results = service.files().list(q="name='aseman' and mimeType='application/vnd.google-apps.folder'", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            folders = folder_results.get('files', [])
            if not folders:
                return JSONResponse({"error": "aseman folder not found"}, status_code=404)

            folder_id = folders[0]['id']
            results = service.files().list(q=f"name='ngc0628_miri_lv3_f2100w_i2d_anchor.fits' and '{folder_id}' in parents", supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
            files = results.get('files', [])
            if not files:
                return JSONResponse({"error": "FITS file not found in aseman folder"}, status_code=404)

            file_id = files[0]['id']
            request = service.files().get_media(fileId=file_id)
            file_data = request.execute()
            with open(cached_file, 'wb') as f:
                f.write(file_data)

        with fits.open(cached_file) as hdul:
            image_data = hdul[1].data.astype(float)

        image_data = np.nan_to_num(image_data)
        color_mapper = LinearColorMapper(palette="Greys256", low=0, high=5)

        plot = figure(title="FITS Image Viewer", x_axis_label="X", y_axis_label="Y", tools="pan,wheel_zoom,box_zoom,reset,save")
        plot.image(image=[image_data], x=0, y=0, dw=image_data.shape[1], dh=image_data.shape[0], color_mapper=color_mapper)
        plot.add_layout(ColorBar(color_mapper=color_mapper, label_standoff=12), 'right')

        script, div = components(plot)
        html_content = f"<h1>FITS File Viewer</h1>{script}\n{div}"
        return HTMLResponse(content=html_content)

    except Exception as e:
        return JSONResponse({"error": f"Failed to display FITS file: {str(e)}"}, status_code=500)

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
