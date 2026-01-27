@echo off
start "Image Processor" python main.py
start "PDF Processor" python pdf_processor.py
echo Both processors started in parallel.
