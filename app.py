from typing import List
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import pytesseract as tess
from PIL import Image, ImageEnhance
import io
import os
import uuid
import asyncio
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Khmer OCR API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure outputs directory exists
os.makedirs("outputs", exist_ok=True)
# Mount the outputs directory to serve static files
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")

# Update this path if Tesseract is installed elsewhere (only needed on Windows)
if os.name == 'nt':
    tess.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

@app.post("/ocr")
async def perform_ocr(file: UploadFile = File(...)):
    try:
        # Read the uploaded image file
        contents = await file.read()
        img = Image.open(io.BytesIO(contents))
        
        # Preprocessing to improve OCR accuracy
        img = img.convert('L') # Grayscale
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2.0) # Increase contrast
        
        # OCR Configuration for Khmer and English
        custom_config = r'-l khm+eng --oem 3 --psm 6'
        
        # Extract text
        text = tess.image_to_string(img, config=custom_config)
        
        return JSONResponse(content={"filename": file.filename, "text": text})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/images-to-pdf")
async def convert_images_to_pdf(request: Request, files: List[UploadFile] = File(...)):
    try:
        images = []
        target_size = None
        
        for i, file in enumerate(files):
            contents = await file.read()
            img = Image.open(io.BytesIO(contents))
            # Convert to RGB to ensure compatibility with PDF format
            img = img.convert("RGB")
            
            # Resize all images to match the dimensions of the first uploaded image
            if i == 0:
                target_size = img.size
            else:
                img = img.resize(target_size, Image.Resampling.LANCZOS)
                
            images.append(img)
            
        if not images:
            return JSONResponse(status_code=400, content={"error": "No images provided"})
            
        # Generate a unique filename for the PDF
        filename = f"{uuid.uuid4().hex}.pdf"
        filepath = os.path.join("outputs", filename)
        
        # Save first image, and append the rest if multiple
        if len(images) == 1:
            images[0].save(filepath, format="PDF")
        else:
            images[0].save(filepath, format="PDF", save_all=True, append_images=images[1:])
            
        # Generate the full URL to access the PDF
        file_url = str(request.base_url) + f"outputs/{filename}"
        
        return JSONResponse(content={
            "message": "PDF created successfully",
            "url": file_url
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/word-to-pdf")
async def convert_word_to_pdf(request: Request, file: UploadFile = File(...)):
    try:
        # Check if the file is a Word document
        if not file.filename.lower().endswith(('.doc', '.docx')):
            return JSONResponse(status_code=400, content={"error": "Please upload a .doc or .docx file"})
            
        # Generate unique filenames
        base_name = uuid.uuid4().hex
        extension = os.path.splitext(file.filename)[1]
        input_filename = f"{base_name}{extension}"
        output_filename = f"{base_name}.pdf"
        
        input_filepath = os.path.join("outputs", input_filename)
        output_filepath = os.path.join("outputs", output_filename)
        
        # Save the uploaded Word file to disk
        contents = await file.read()
        with open(input_filepath, "wb") as f:
            f.write(contents)
            
        # Convert Word to PDF (OS dependent)
        if os.name == 'nt':
            # Windows: use docx2pdf
            from docx2pdf import convert
            await asyncio.to_thread(convert, input_filepath, output_filepath)
        else:
            # Linux (Render): use LibreOffice
            process = await asyncio.create_subprocess_exec(
                "libreoffice", "--headless", "--nologo", "--nofirststartwizard", 
                "--convert-to", "pdf", "--outdir", "outputs", input_filepath,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                raise Exception(f"LibreOffice conversion failed: {stderr.decode()}")
        
        # Generate the full URL to access the PDF
        file_url = str(request.base_url) + f"outputs/{output_filename}"
        
        # Optional: remove the input word file to save space
        if os.path.exists(input_filepath):
            os.remove(input_filepath)
            
        return JSONResponse(content={
            "message": "Word to PDF conversion successful",
            "url": file_url
        })
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
