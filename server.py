from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from pathlib import Path
import base64
from datetime import datetime
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv
import mimetypes
from PIL import Image
import time

# Load environment variables
load_dotenv()

# Import configuration
import config

app = Flask(__name__)
CORS(app)

# Create necessary directories
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'
VIDEO_FOLDER = 'videos'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(GENERATED_FOLDER, exist_ok=True)
os.makedirs(VIDEO_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['GENERATED_FOLDER'] = GENERATED_FOLDER
app.config['VIDEO_FOLDER'] = VIDEO_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg, gif, webp'}), 400
        
        # Get form data
        model = request.form.get('model')
        prompt = request.form.get('prompt')
        negative_prompt = request.form.get('negative_prompt', '')
        n = int(request.form.get('n', 1))
        prompt_extend = request.form.get('prompt_extend', 'true').lower() == 'true'
        watermark = request.form.get('watermark', 'false').lower() == 'true'
        seed = request.form.get('seed')
        
        # Convert seed to int if provided
        if seed and seed.strip():
            try:
                seed = int(seed)
                if seed < 0 or seed > 2147483647:
                    return jsonify({'error': 'Seed must be between 0 and 2147483647'}), 400
            except ValueError:
                return jsonify({'error': 'Invalid seed value'}), 400
        else:
            seed = None
        
        # Validate n parameter
        if n < 1 or n > 6:
            return jsonify({'error': 'Number of images must be between 1 and 6'}), 400
        
        if not model or not prompt:
            return jsonify({'error': 'Model and prompt are required'}), 400
        
        # Save uploaded file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        upload_filename = f'upload_{timestamp}.{file_ext}'
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        file.save(upload_path)
        
        print(f"Image uploaded: {upload_path}")
        print(f"Model: {model}")
        print(f"Prompt: {prompt}")
        print(f"Negative prompt: {negative_prompt}")
        print(f"Number of images: {n}")
        print(f"Seed: {seed}")
        print(f"Prompt extend: {prompt_extend}")
        print(f"Watermark: {watermark}")
        
        # TODO: Integrate with actual AI model API
        # For now, this is a placeholder that would call the qwen-image or qwen-wan API
        # You would need to replace this with actual API calls to your model service
        
        # Call API based on selected model
        model_config = config.MODELS[model]
        model_version = model_config['version']
        api_type = model_config['api_type']
        
        was_padded = False
        if api_type == 'qwen':
            image_urls, was_padded = call_qwen_image_api(
                upload_path, prompt, model_version, n,
                negative_prompt, seed, prompt_extend, watermark
            )
        elif api_type == 'wanx':
            image_urls, was_padded = call_wanx_image_api(
                upload_path, prompt, model_version, n,
                negative_prompt, seed, watermark
            )
        elif api_type == 'i2v':
            # Get video-specific parameters
            resolution = request.form.get('resolution', '720P')
            duration = int(request.form.get('duration', 5))
            audio_enabled = request.form.get('audio', 'true').lower() == 'true'
            
            video_url, was_padded = call_i2v_api(
                upload_path, prompt, model_version,
                resolution, duration, audio_enabled,
                negative_prompt, seed, prompt_extend, watermark
            )
            
            # Download video
            video_filename = f'video_{timestamp}.mp4'
            video_path = os.path.join(app.config['VIDEO_FOLDER'], video_filename)
            
            # Use session with retry logic for video download
            session = create_session_with_retries()
            proxies = config.get_proxies()
            
            print(f"[Video Download] Downloading from: {video_url}")
            
            # Retry video download
            for attempt in range(config.MAX_RETRIES):
                try:
                    video_response = session.get(video_url, timeout=120, proxies=proxies)
                    if video_response.status_code == 200:
                        with open(video_path, 'wb') as f:
                            f.write(video_response.content)
                        print(f"[Video Download] Successfully downloaded video ({len(video_response.content)} bytes)")
                        break
                    else:
                        raise Exception(f"Failed to download video: HTTP {video_response.status_code}")
                except requests.exceptions.ConnectionError as e:
                    print(f"[Video Download] Connection error on attempt {attempt + 1}: {str(e)}")
                    if attempt < config.MAX_RETRIES - 1:
                        print(f"[Video Download] Retrying in {config.RETRY_DELAY} seconds...")
                        time.sleep(config.RETRY_DELAY)
                    else:
                        raise Exception(
                            f"Failed to download video after {config.MAX_RETRIES} attempts. "
                            "Please check your network connection and proxy settings."
                        )
                except requests.exceptions.Timeout as e:
                    print(f"[Video Download] Timeout on attempt {attempt + 1}: {str(e)}")
                    if attempt < config.MAX_RETRIES - 1:
                        print(f"[Video Download] Retrying in {config.RETRY_DELAY} seconds...")
                        time.sleep(config.RETRY_DELAY)
                    else:
                        raise Exception(f"Video download timeout after {config.MAX_RETRIES} attempts")
            
            return jsonify({
                'success': True,
                'video_url': f'/videos/{video_filename}',
                'model_used': model,
                'model_version': model_version,
                'resolution': resolution,
                'duration': duration,
                'audio_enabled': audio_enabled,
                'padded': was_padded
            })
        else:
            return jsonify({'error': 'Invalid model type'}), 400
        
        if not image_urls or len(image_urls) == 0:
            return jsonify({'error': 'No images generated'}), 500
        
        # Download all generated images from URLs
        local_image_urls = []
        for idx, api_image_url in enumerate(image_urls):
            generated_filename = f'generated_{timestamp}_{idx + 1}.png'
            generated_path = os.path.join(app.config['GENERATED_FOLDER'], generated_filename)
            
            # Download image from API response URL
            image_response = requests.get(api_image_url, timeout=30)
            if image_response.status_code == 200:
                with open(generated_path, 'wb') as f:
                    f.write(image_response.content)
                local_image_urls.append(f'/generated/{generated_filename}')
            else:
                print(f"Warning: Failed to download image {idx + 1}")
        
        if not local_image_urls:
            return jsonify({'error': 'Failed to download generated images'}), 500
        
        return jsonify({
            'success': True,
            'images': local_image_urls,
            'model_used': model,
            'model_version': model_version,
            'count': len(local_image_urls),
            'seed': seed,
            'padded': was_padded
        })
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def encode_image_to_base64(image_path):
    """Encode image file to base64 format"""
    mime_type, _ = mimetypes.guess_type(image_path)
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return f"data:{mime_type};base64,{encoded_string}"

def pad_image_to_minimum(image_path, min_dimension=config.IMAGE_MIN_DIMENSION):
    """
    Pad image to meet minimum dimension requirements without distorting aspect ratio
    
    Args:
        image_path: Path to the image file
        min_dimension: Minimum required dimension (default: 384)
    
    Returns:
        Path to padded image (or original if no padding needed)
    """
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Check if padding is needed
        if width >= min_dimension and height >= min_dimension:
            return image_path
        
        # Calculate new dimensions
        new_width = max(width, min_dimension)
        new_height = max(height, min_dimension)
        
        # Create new image with padding
        # Use a neutral background color (black or match edge color)
        padded_img = Image.new('RGB', (new_width, new_height), (0, 0, 0))
        
        # Calculate position to paste original image (center it)
        paste_x = (new_width - width) // 2
        paste_y = (new_height - height) // 2
        
        # Convert to RGB if necessary (for PNG with transparency)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Paste original image onto padded canvas
        padded_img.paste(img, (paste_x, paste_y))
        
        # Save padded image
        padded_path = image_path.rsplit('.', 1)[0] + '_padded.jpg'
        padded_img.save(padded_path, 'JPEG', quality=95)
        
        print(f"[Image Padding] Original size: {width}x{height}")
        print(f"[Image Padding] Padded to: {new_width}x{new_height}")
        print(f"[Image Padding] Saved to: {padded_path}")
        
        return padded_path

def validate_image(image_path, auto_pad=True):
    """Validate image dimensions and size"""
    # Check file size
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if file_size_mb > config.IMAGE_MAX_SIZE_MB:
        raise ValueError(f"Image size ({file_size_mb:.2f}MB) exceeds maximum allowed size ({config.IMAGE_MAX_SIZE_MB}MB)")
    
    # Check dimensions
    with Image.open(image_path) as img:
        width, height = img.size
        
        # Check if dimensions are too large
        if width > config.IMAGE_MAX_DIMENSION or height > config.IMAGE_MAX_DIMENSION:
            raise ValueError(f"Image dimensions ({width}x{height}) are too large. Maximum: {config.IMAGE_MAX_DIMENSION}x{config.IMAGE_MAX_DIMENSION}")
        
        # Check if dimensions are too small and auto_pad is disabled
        if not auto_pad and (width < config.IMAGE_MIN_DIMENSION or height < config.IMAGE_MIN_DIMENSION):
            raise ValueError(f"Image dimensions ({width}x{height}) are too small. Minimum: {config.IMAGE_MIN_DIMENSION}x{config.IMAGE_MIN_DIMENSION}")
    
    return True

def create_session_with_retries():
    """Create a requests session with retry logic"""
    session = requests.Session()
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=config.MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS", "TRACE"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def call_qwen_image_api(image_path, prompt, model_name=config.QWEN_IMAGE_EDIT_PLUS, n=1, 
                        negative_prompt=None, seed=None, prompt_extend=True, watermark=False):
    """
    Call Qwen-Image API to generate image based on reference style
    
    Args:
        image_path: Path to the reference image
        prompt: Text prompt for image generation
        model_name: Model to use (default: qwen-image-edit-plus)
        n: Number of images to generate (1-6 for plus model)
        negative_prompt: Negative prompt (what to avoid)
        seed: Random seed for reproducibility (0-2147483647)
        prompt_extend: Enable intelligent prompt optimization
        watermark: Add Qwen-Image watermark
    
    Returns:
        List of generated image URLs
    """
    try:
        # Validate API key
        config.validate_api_key()
        
        # Validate image (will raise exception if too large)
        validate_image(image_path, auto_pad=True)
        
        # Pad image if dimensions are too small
        original_path = image_path
        image_path = pad_image_to_minimum(image_path)
        was_padded = (image_path != original_path)
        
        # Encode image to base64
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_base64},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "n": n,
                "negative_prompt": negative_prompt if negative_prompt else config.DEFAULT_PARAMS['negative_prompt'],
                "prompt_extend": prompt_extend,
                "watermark": watermark
            }
        }
        
        # Add seed if provided
        if seed is not None:
            payload["parameters"]["seed"] = seed
        
        print(f"[Qwen-Image] Processing with model: {model_name}")
        print(f"[Qwen-Image] Prompt: {prompt}")
        print(f"[Qwen-Image] Negative prompt: {negative_prompt if negative_prompt else config.DEFAULT_PARAMS['negative_prompt']}")
        print(f"[Qwen-Image] Generating {n} image(s)...")
        print(f"[Qwen-Image] Seed: {seed if seed is not None else 'Random'}")
        print(f"[Qwen-Image] Prompt extend: {prompt_extend}")
        if prompt_extend and seed is not None:
            print(f"[Qwen-Image] WARNING: Prompt extend is ON with seed={seed}. This may reduce reproducibility as prompts are AI-rewritten.")
        print(f"[Qwen-Image] Watermark: {watermark}")
        print(f"[Qwen-Image] API URL: {config.API_BASE_URL_QWEN}")
        
        # Create session with retry logic
        session = create_session_with_retries()
        
        # Get proxy settings
        proxies = config.get_proxies()
        if proxies:
            print(f"[Qwen-Image] Using proxy: {proxies}")
        
        # Make API request with retries
        for attempt in range(config.MAX_RETRIES):
            try:
                print(f"[Qwen-Image] Attempt {attempt + 1}/{config.MAX_RETRIES}...")
                
                response = session.post(
                    config.API_BASE_URL_QWEN,
                    headers=config.get_headers(),
                    json=payload,
                    timeout=config.REQUEST_TIMEOUT,
                    proxies=proxies
                )
                
                # Check response
                if response.status_code == 200:
                    result = response.json()
                    if 'output' in result and 'choices' in result['output']:
                        image_urls = []
                        for choice in result['output']['choices']:
                            if 'message' in choice and 'content' in choice['message']:
                                for content_item in choice['message']['content']:
                                    if 'image' in content_item:
                                        image_urls.append(content_item['image'])
                        
                        print(f"[Qwen-Image] Successfully generated {len(image_urls)} image(s)")
                        return image_urls, was_padded
                    else:
                        raise Exception("Unexpected response format from API")
                else:
                    error_data = response.json()
                    error_msg = error_data.get('message', 'Unknown error')
                    error_code = error_data.get('code', 'Unknown')
                    raise Exception(f"API Error [{error_code}]: {error_msg}")
                    
            except requests.exceptions.ConnectionError as e:
                print(f"[Qwen-Image] Connection error on attempt {attempt + 1}: {str(e)}")
                if attempt < config.MAX_RETRIES - 1:
                    print(f"[Qwen-Image] Retrying in {config.RETRY_DELAY} seconds...")
                    time.sleep(config.RETRY_DELAY)
                else:
                    raise Exception(
                        f"Failed to connect to API after {config.MAX_RETRIES} attempts. "
                        "Please check: 1) Internet connection, 2) Firewall settings, "
                        "3) Proxy configuration (set HTTP_PROXY/HTTPS_PROXY if needed), "
                        "4) VPN connection if required"
                    )
            except requests.exceptions.Timeout as e:
                print(f"[Qwen-Image] Timeout on attempt {attempt + 1}: {str(e)}")
                if attempt < config.MAX_RETRIES - 1:
                    print(f"[Qwen-Image] Retrying in {config.RETRY_DELAY} seconds...")
                    time.sleep(config.RETRY_DELAY)
                else:
                    raise Exception(f"Request timeout after {config.MAX_RETRIES} attempts")
    
    except Exception as e:
        print(f"[Qwen-Image] Error: {str(e)}")
        raise

def call_qwen_wan_api(image_path, prompt, model_name, n=1, negative_prompt=None, seed=None, 
                      prompt_extend=True, watermark=False):
    """
    Deprecated: This function is kept for backward compatibility
    Use call_wanx_image_api for Wanxiang model instead
    """
    return call_qwen_image_api(image_path, prompt, model_name, n, 
                               negative_prompt, seed, prompt_extend, watermark)

def call_wanx_image_api(image_path, prompt, model_name, n=1, negative_prompt=None, 
                        seed=None, watermark=False):
    """
    Call Wanxiang 2.5 async API for image editing
    
    Args:
        image_path: Path to the reference image
        prompt: Text prompt for image generation
        model_name: Model to use (wan2.5-i2i-preview)
        n: Number of images to generate (1-4)
        negative_prompt: Negative prompt (what to avoid)
        seed: Random seed for reproducibility
        watermark: Add AI-generated watermark
    
    Returns:
        Tuple of (image_urls, was_padded)
    """
    try:
        # Validate API key
        config.validate_api_key()
        
        # Validate image
        validate_image(image_path, auto_pad=True)
        
        # Pad image if needed
        original_path = image_path
        image_path = pad_image_to_minimum(image_path)
        was_padded = (image_path != original_path)
        
        # Encode image to base64 or use URL
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request payload for Wanxiang async API
        payload = {
            "model": model_name,
            "input": {
                "prompt": prompt,
                "images": [image_base64]  # Wanx API uses images array
            },
            "parameters": {
                "n": min(n, 4)  # Wanxiang max is 4
            }
        }
        
        # Add optional parameters
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        
        if seed is not None:
            payload["parameters"]["seed"] = seed
        
        if watermark:
            payload["parameters"]["watermark"] = True
        
        print(f"[Wanxiang] Processing with model: {model_name}")
        print(f"[Wanxiang] Prompt: {prompt}")
        print(f"[Wanxiang] Generating {n} image(s)...")
        print(f"[Wanxiang] Seed: {seed if seed is not None else 'Random'}")
        print(f"[Wanxiang] API URL: {config.API_BASE_URL_WANX}")
        print(f"[Wanxiang] Note: This is an async API, results will take 1-2 minutes")
        
        # Create session
        session = create_session_with_retries()
        proxies = config.get_proxies()
        
        # Step 1: Create async task
        headers = config.get_headers()
        headers['X-DashScope-Async'] = 'enable'  # Required for async API
        
        print(f"[Wanxiang] Creating async task...")
        response = session.post(
            config.API_BASE_URL_WANX,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=proxies
        )
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('message', 'Unknown error')
            error_code = error_data.get('code', 'Unknown')
            raise Exception(f"API Error [{error_code}]: {error_msg}")
        
        result = response.json()
        task_id = result.get('output', {}).get('task_id')
        
        if not task_id:
            raise Exception("Failed to get task_id from API response")
        
        print(f"[Wanxiang] Task created: {task_id}")
        print(f"[Wanxiang] Polling for results (this may take 1-2 minutes)...")
        
        # Step 2: Poll for results
        max_attempts = 60  # 60 attempts * 5 seconds = 5 minutes max
        poll_interval = 5  # seconds
        
        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            
            # Query task status
            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            query_response = session.get(
                query_url,
                headers=config.get_headers(),
                timeout=30,
                proxies=proxies
            )
            
            if query_response.status_code != 200:
                print(f"[Wanxiang] Query error: {query_response.status_code}")
                continue
            
            task_result = query_response.json()
            task_status = task_result.get('output', {}).get('task_status')
            
            print(f"[Wanxiang] Attempt {attempt + 1}/{max_attempts} - Status: {task_status}")
            
            if task_status == 'SUCCEEDED':
                # Extract image URLs
                results = task_result.get('output', {}).get('results', [])
                image_urls = [item.get('url') for item in results if item.get('url')]
                
                if image_urls:
                    print(f"[Wanxiang] Successfully generated {len(image_urls)} image(s)")
                    return image_urls, was_padded
                else:
                    raise Exception("No image URLs in successful response")
            
            elif task_status == 'FAILED':
                error_code = task_result.get('output', {}).get('code', 'Unknown')
                error_msg = task_result.get('output', {}).get('message', 'Unknown error')
                raise Exception(f"Task failed [{error_code}]: {error_msg}")
            
            elif task_status in ['PENDING', 'RUNNING']:
                # Continue polling
                continue
            else:
                raise Exception(f"Unknown task status: {task_status}")
        
        raise Exception(f"Task timeout after {max_attempts * poll_interval} seconds")
    
    except Exception as e:
        print(f"[Wanxiang] Error: {str(e)}")
        raise

def call_i2v_api(image_path, prompt, model_name, resolution='720P', duration=5, 
                 audio_enabled=True, negative_prompt=None, seed=None, 
                 prompt_extend=True, watermark=False):
    """
    Call Wanxiang Image-to-Video async API
    
    Args:
        image_path: Path to the reference image
        prompt: Text prompt for video generation
        model_name: Model to use (wan2.5-i2v-preview)
        resolution: Video resolution (480P/720P/1080P)
        duration: Video duration in seconds (5 or 10)
        audio_enabled: Enable audio generation
        negative_prompt: Negative prompt
        seed: Random seed
        prompt_extend: Enable prompt optimization
        watermark: Add watermark
    
    Returns:
        Tuple of (video_url, was_padded)
    """
    try:
        # Validate API key
        config.validate_api_key()
        
        # Validate image
        validate_image(image_path, auto_pad=True)
        
        # Pad image if needed
        original_path = image_path
        image_path = pad_image_to_minimum(image_path)
        was_padded = (image_path != original_path)
        
        # Encode image to base64
        image_base64 = encode_image_to_base64(image_path)
        
        # Prepare request payload
        payload = {
            "model": model_name,
            "input": {
                "prompt": prompt,
                "img_url": image_base64
            },
            "parameters": {
                "resolution": resolution,
                "duration": duration,
                "prompt_extend": prompt_extend
            }
        }
        
        # Add audio parameter (default enabled for wan2.5)
        if audio_enabled:
            payload["parameters"]["audio"] = True
        else:
            payload["parameters"]["audio"] = False
        
        # Add optional parameters
        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        
        if seed is not None:
            payload["parameters"]["seed"] = seed
        
        if watermark:
            payload["parameters"]["watermark"] = True
        
        print(f"[I2V] Processing with model: {model_name}")
        print(f"[I2V] Prompt: {prompt}")
        print(f"[I2V] Resolution: {resolution}, Duration: {duration}s, Audio: {audio_enabled}")
        print(f"[I2V] API URL: {config.API_BASE_URL_I2V}")
        print(f"[I2V] Note: Video generation typically takes 1-5 minutes")
        
        # Create session
        session = create_session_with_retries()
        proxies = config.get_proxies()
        
        # Step 1: Create async task
        headers = config.get_headers()
        headers['X-DashScope-Async'] = 'enable'  # Required for async API
        
        print(f"[I2V] Creating async video generation task...")
        response = session.post(
            config.API_BASE_URL_I2V,
            headers=headers,
            json=payload,
            timeout=30,
            proxies=proxies
        )
        
        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get('message', 'Unknown error')
            error_code = error_data.get('code', 'Unknown')
            raise Exception(f"API Error [{error_code}]: {error_msg}")
        
        result = response.json()
        task_id = result.get('output', {}).get('task_id')
        
        if not task_id:
            raise Exception("Failed to get task_id from API response")
        
        print(f"[I2V] Task created: {task_id}")
        print(f"[I2V] Polling for results (please wait 1-5 minutes)...")
        
        # Step 2: Poll for results
        max_attempts = 100  # 100 attempts * 6 seconds = 10 minutes max
        poll_interval = 6  # seconds
        
        for attempt in range(max_attempts):
            time.sleep(poll_interval)
            
            # Query task status
            query_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            query_response = session.get(
                query_url,
                headers=config.get_headers(),
                timeout=30,
                proxies=proxies
            )
            
            if query_response.status_code != 200:
                print(f"[I2V] Query error: {query_response.status_code}")
                continue
            
            task_result = query_response.json()
            task_status = task_result.get('output', {}).get('task_status')
            
            print(f"[I2V] Attempt {attempt + 1}/{max_attempts} - Status: {task_status}")
            
            if task_status == 'SUCCEEDED':
                # Extract video URL
                video_url = task_result.get('output', {}).get('video_url')
                
                if video_url:
                    print(f"[I2V] Successfully generated video")
                    return video_url, was_padded
                else:
                    raise Exception("No video URL in successful response")
            
            elif task_status == 'FAILED':
                error_code = task_result.get('output', {}).get('code', 'Unknown')
                error_msg = task_result.get('output', {}).get('message', 'Unknown error')
                raise Exception(f"Task failed [{error_code}]: {error_msg}")
            
            elif task_status in ['PENDING', 'RUNNING']:
                # Continue polling
                continue
            else:
                raise Exception(f"Unknown task status: {task_status}")
        
        raise Exception(f"Task timeout after {max_attempts * poll_interval} seconds")
    
    except Exception as e:
        print(f"[I2V] Error: {str(e)}")
        raise

@app.route('/videos/<filename>')
def serve_video(filename):
    return send_from_directory(app.config['VIDEO_FOLDER'], filename)

@app.route('/generated/<filename>')
def serve_generated_image(filename):
    return send_from_directory(app.config['GENERATED_FOLDER'], filename)

@app.route('/uploads/<filename>')
def serve_uploaded_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    print("Starting Flask server...")
    print("Open http://localhost:8080 in your browser")
    app.run(debug=True, host='0.0.0.0', port=8080)
