from fastapi import FastAPI
import gradio as gr
from app import demo

app = FastAPI()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

import os
print(f"Starting Vercel App... Filesystem: {'Read-Only' if not os.access('/', os.W_OK) else 'Writable'}")
app = gr.mount_gradio_app(app, demo, path="/")
