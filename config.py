import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Load API key from environment variable
# Set your API key in environment: export DASHSCOPE_API_KEY="sk-xxxx"
DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY', '')

# Proxy settings (if needed)
HTTP_PROXY = os.getenv('HTTP_PROXY', '')
HTTPS_PROXY = os.getenv('HTTPS_PROXY', '')

# API Configuration
# Beijing region (default)
API_BASE_URL_QWEN = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
API_BASE_URL_WANX = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis'
API_BASE_URL_I2V = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis'

# Uncomment below for Singapore region
# API_BASE_URL_QWEN = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation'
# API_BASE_URL_WANX = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/image2image/image-synthesis'
# API_BASE_URL_I2V = 'https://dashscope-intl.aliyuncs.com/api/v1/services/aigc/video-generation/video-synthesis'

# Model names
QWEN_IMAGE_EDIT_PLUS = 'qwen-image-edit-plus'
QWEN_IMAGE_EDIT_PLUS_LATEST = 'qwen-image-edit-plus-2025-10-30'
QWEN_IMAGE_EDIT = 'qwen-image-edit'
WANX_IMAGE_EDIT = 'wan2.5-i2i-preview'
WANX_IMAGE_TO_VIDEO = 'wan2.5-i2v-preview'

# Model display information
MODELS = {
    'qwen-image': {
        'name': 'Qwen-Image-Edit-Plus',
        'version': 'qwen-image-edit-plus-2025-10-30',
        'description': 'Qwen image editing and enhancement',
        'api_type': 'qwen',
        'api_url': 'API_BASE_URL_QWEN'
    },
    'wanx': {
        'name': 'Wanxiang 2.5',
        'version': 'wan2.5-i2i-preview',
        'description': 'Wanxiang multi-image fusion and editing',
        'api_type': 'wanx',
        'api_url': 'API_BASE_URL_WANX'
    },
    'i2v': {
        'name': 'Wanxiang Image-to-Video 2.5',
        'version': 'wan2.5-i2v-preview',
        'description': 'Generate video from image with audio',
        'api_type': 'i2v',
        'api_url': 'API_BASE_URL_I2V'
    }
}

# Default parameters
DEFAULT_PARAMS = {
    'n': 1,  # Number of images to generate (1-6 for plus model, 1 for basic)
    'negative_prompt': '低分辨率、错误、最差质量、低质量、残缺、多余的手指、比例不良',
    'prompt_extend': True,  # Enable intelligent prompt optimization
    # NOTE: For reproducible results with same seed, set prompt_extend to False
    # When prompt_extend is True, the AI rewrites prompts, causing variations even with same seed
    'watermark': False  # Set to True to add Qwen-Image watermark
}

# Image constraints
IMAGE_MAX_SIZE_MB = 10
IMAGE_MIN_DIMENSION = 384  # pixels
IMAGE_MAX_DIMENSION = 3072  # pixels
ALLOWED_IMAGE_FORMATS = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp']

# Upload and output directories
UPLOAD_FOLDER = 'uploads'
GENERATED_FOLDER = 'generated'

def validate_api_key():
    """Check if API key is configured"""
    if not DASHSCOPE_API_KEY:
        raise ValueError(
            "DASHSCOPE_API_KEY not found in environment variables.\n"
            "Please set it using: export DASHSCOPE_API_KEY='your-api-key'"
        )
    return True

def get_headers():
    """Get request headers with authorization"""
    return {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DASHSCOPE_API_KEY}'
    }

def get_proxies():
    """Get proxy configuration if available"""
    proxies = {}
    if HTTP_PROXY:
        proxies['http'] = HTTP_PROXY
    if HTTPS_PROXY:
        proxies['https'] = HTTPS_PROXY
    return proxies if proxies else None

# Request settings
REQUEST_TIMEOUT = 120  # seconds
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds
