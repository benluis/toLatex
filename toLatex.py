import base64
import requests


def toLatex(image_path, output_file, api_key):
    """"
    Function to convert a single image to LaTeX using OpenAI's API.
    """
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    base64_image = encode_image(image_path)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Please generate a complete LaTeX document for this image, "
                                "including the document structure with \\documentclass, "
                                "\\begin{document}, and \\end{document}. "
                                "Ensure that the LaTeX code can be compiled directly."
                                "Do not write anything else other than the latex code."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1500
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    if response.status_code == 200:
        latex_code = response.json()['choices'][0]['message']['content']

        with open(output_file, 'w') as file:
            file.write(latex_code)

        print(f"LaTeX code has been saved to '{output_file}'")
    else:
        print(f"Error: {response.status_code} - {response.text}")