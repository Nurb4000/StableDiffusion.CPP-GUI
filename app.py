import os
import subprocess
import random
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, after_this_request
from PIL import Image
import io
import base64
import tempfile
import shutil

app = Flask(__name__)

# Configuration - easily add or modify models here
MODEL_CONFIGS = {
    "z Image Turbo": {
        "command": ".bin/sd-cli",
        "args": [
            "--diffusion-model", "./models/z_image_turbo-Q8_0.gguf",
            "--llm", "./models/qwen_3_4b-Q8_0.gguf",
            "-H", "{height}",
            "-W", "{width}",
            "--vae", "./models/ae.safetensors",
            "--vae-conv-direct",
            "--sampling-method", "euler",
            "--scheduler", "smoothstep",
            "--steps", "{steps}",
            "--cfg-scale", "1",
            "-p", "{prompt}",
            "-s", "{seed}"
        ]
    },
    "RealVisXL_V5": {
        "command": "./bin/sd-cli",
        "args": [
            "-m", "./models/RealVisXL_V5.0_fp32.safetensors",
            "-p", "{prompt}",
            "-H", "{height}",
            "-W", "{width}",
            "--sampling-method", "dpm++2m",
            "--scheduler", "karras",
            "--steps", "{steps}",
            "-s", "{seed}"
        ]
    },
    "4GB Improved": {
        "command": "./bin/sd-cli",
        "args": [
            "-m", "./models/sdxl4GB2GBImprovedFP8_fp8FullCheckpoint.safetensors",
            "-p", "{prompt}",
            "-H", "{height}",
            "-W", "{width}",
            "--sampling-method", "dpm++2m",
            "--scheduler", "karras",
            "--steps", "{steps}",
            "-s", "{seed}"
        ]
    }
}

def get_loras():
    lora_dir = "./loras"
    loras = []
    try:
        if os.path.exists(lora_dir) and os.path.isdir(lora_dir):
            for f in os.listdir(lora_dir):
                if os.path.isfile(os.path.join(lora_dir, f)):
                    # Remove extension
                    name = os.path.splitext(f)[0]
                    loras.append(name)
    except Exception as e:
        print(f"Error scanning loras directory: {e}")
    return sorted(loras)

def generate_filename(seed=None):
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"sd_{timestamp}_{seed}"

def clean_temp_files(files):
    for file in files:
        try:
            if file and os.path.exists(file):
                os.remove(file)
        except Exception as e:
            print(f"Error deleting file {file}: {e}")

@app.route('/')
def index():
    return render_template('index.html', 
                         models=list(MODEL_CONFIGS.keys()),
                         loras=get_loras())

@app.route('/generate', methods=['POST'])
def generate():
    # Get form data
    data = request.json
    prompt = data.get('prompt', '')
    height = data.get('height', 768)
    width = data.get('width', 1024)
    steps = data.get('steps', 10)
    seed = data.get('seed')
    use_random_seed = data.get('useRandomSeed', True)
    filename = data.get('filename', '')
    model = data.get('model', list(MODEL_CONFIGS.keys())[0])
    lora_file = data.get('lora', '')

    # Generate random seed if needed
    if use_random_seed or not seed:
        seed = random.randint(0, 2**32 - 1)
    else:
        try:
            seed = int(seed)
        except ValueError:
            return jsonify({'error': 'Seed must be an integer'}), 400

    # Generate filename if needed
    if not filename:
        filename = generate_filename(seed)
    base_filename = os.path.join('output', filename)
    
    # Create output directory if it doesn't exist
    os.makedirs('output', exist_ok=True)

    # Get model config
    if model not in MODEL_CONFIGS:
        return jsonify({'error': 'Invalid model selected'}), 400

    config = MODEL_CONFIGS[model]
    command = [config['command']]
    
    # Add lora model directory if lora file is selected
    if lora_file:
        command.extend(['--lora-model-dir', './loras'])
    
    # Format prompt with lora if selected
    formatted_prompt = f"{prompt} <lora:{lora_file}:1>" if lora_file else prompt
    
    # Build command arguments
    args = [arg.format(
        prompt=formatted_prompt,
        height=height,
        width=width,
        steps=steps,
        seed=seed
    ) for arg in config['args']]
    
    command.extend(args)
    
    # Add output file
    output_image = f"{base_filename}.png"
    command.extend(['-o', output_image])

    # Run the command
    try:
        print("Running command:", " ".join(command))
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Read and resize image for display
        img = Image.open(output_image)
        display_size = (512, 512)
        img.thumbnail(display_size, Image.LANCZOS)
        
        # Convert to base64 for display
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Save parameters
        params = {
            'prompt': formatted_prompt,
            'height': height,
            'width': width,
            'steps': steps,
            'seed': seed,
            'model': model,
            'lora': lora_file if lora_file else "None",
            'filename': filename,
            'command': ' '.join(command)
        }
        
        with open(f"{base_filename}.txt", 'w') as f:
            for key, value in params.items():
                if key != 'command':
                    f.write(f"{key}: {value}\n")
            f.write(f"\nFull command:\n{params['command']}")
        
        return jsonify({
            'image': f"data:image/png;base64,{img_str}",
            'filename': filename,
            'seed': seed
        })
        
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f"Generation failed: {e.stderr}"}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<filename>')
def download(filename):
    base_path = os.path.join('output', filename)
    image_path = f"{base_path}.png"
    text_path = f"{base_path}.txt"

    @after_this_request
    def remove_files(response):
        try:
            clean_temp_files([image_path, text_path])
        except Exception as e:
            print(f"Error removing files: {e}")
        return response

    # Create zip file
    import zipfile
    from io import BytesIO
    
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w') as zf:
        if os.path.exists(image_path):
            zf.write(image_path, f"{filename}.png")
        if os.path.exists(text_path):
            zf.write(text_path, f"{filename}.txt")
    
    memory_file.seek(0)
    
    # Use attachment_filename for older Flask versions
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        # attachment_filename=f"{filename}.zip" # Use this for Flask < 2.0
        download_name=f"{filename}.zip" # Use this for Flask > 2.0
        
    )

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
