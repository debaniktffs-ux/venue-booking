from fastapi import FastAPI
import gradio as gr
from app import demo

app = FastAPI()

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

# Mount the Gradio app to the FastAPI instance
app = gr.mount_gradio_app(app, demo, path="/")
