from flask import Flask, request, render_template, redirect, url_for, flash
from preprocessing import preprocess_image_for_ocr, pdf_to_images, create_temp_folder
from toLatex import toLatex
from markupsafe import Markup
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def process_image(image_path, output_file, api_key):
    """
    Preprocess the image and convert it to LaTeX.
    """
    print(f"Processing image: {image_path}")

    # Preprocess the image
    preprocessed_image = preprocess_image_for_ocr(image_path)

    # Convert the preprocessed image to LaTeX
    toLatex(preprocessed_image, output_file, api_key)

    print(f"Image processing complete. LaTeX output saved to '{output_file}'")

def process_pdf(pdf_path, output_file_base, api_key):
    """
    Convert PDF to images, preprocess each image, and convert it to LaTeX.
    Save LaTeX output for each page with page number appended to the output file name.
    """
    print(f"Processing PDF: {pdf_path}")

    # Create a temporary folder to store the PDF images
    temp_folder = create_temp_folder()

    # Convert PDF pages to images and store them in the temp folder
    pdf_images = pdf_to_images(pdf_path, temp_folder)

    output_files = []

    # Process each image and output the LaTeX to separate files
    for page_number, image_path in enumerate(pdf_images, start=1):
        print(f"Processing page {page_number} image: {image_path}")

        # Preprocess the image for OCR
        preprocessed_image = preprocess_image_for_ocr(image_path)

        # Create the output file name for this page (e.g., output_file_base_1.txt, output_file_base_2.txt)
        page_output_file = f"{output_file_base}_{page_number}.txt"

        # Convert the preprocessed image to LaTeX
        toLatex(preprocessed_image, page_output_file, api_key)

        output_files.append(page_output_file)
        print(f"LaTeX output for page {page_number} saved to '{page_output_file}'")

    print("PDF processing complete.")
    return output_files

@app.route('/', methods=['GET', 'POST'])
def index():
    output_files = []
    if request.method == 'POST':
        input_type = request.form['input_type'].strip().lower()
        file = request.files['file']
        api_key = request.form['api_key'].strip()
        output_file_base = request.form['output_file_base'].strip()

        file_extension = os.path.splitext(file.filename)[1].lower()
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('index'))
        
        if input_type == 'pdf':
            if file_extension != '.pdf':
                flash('Invalid file format. Please upload a PDF file.', 'error')
                return redirect(url_for('index'))

        elif input_type == 'image':
            if file_extension not in ['.png', '.jpg', '.jpeg']:
                flash('Invalid file format. Please upload an image file (PNG, JPG, or JPEG).', 'error')
                return redirect(url_for('index'))

        else:
            flash(f"Invalid input type: {input_type}. Please select 'pdf' or 'image'.", "error")
            return redirect(url_for('index'))

        # Save the uploaded file directly with the user's provided name
        save_path = os.path.join(os.getcwd(), file.filename)
        file.save(save_path)

        try:
            if input_type == 'pdf':
                output_files = process_pdf(save_path, output_file_base, api_key)
            elif input_type == 'image':
                output_file = f"{output_file_base}_1.txt"
                process_image(save_path, output_file, api_key)
                output_files.append(output_file)
            else:
                flash(f"Invalid input type: {input_type}. Please enter 'pdf' or 'image'.", "error")
                return redirect(url_for('index'))

            return redirect(url_for('output', output_files=output_files))

        except Exception as e:
            print(e)
            flash(f"An error occurred during processing. Please check your API key and try again", "error")
            return redirect(url_for('index'))

    return render_template('index.html', output_files=output_files)

@app.template_filter('get_file_content')
def get_file_content(file_path):
    with open(file_path, 'r') as file:
        return Markup(file.read().replace('\n', '<br>'))
    
@app.route('/output')
def output():
    output_files = request.args.getlist('output_files')
    return render_template('output.html', output_files=output_files)

if __name__ == "__main__":
    app.run(debug=True)