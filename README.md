# AI Image & Video Generation Web App

A web application for AI-powered image editing and video generation using Alibaba Cloud's Qwen and Wanxiang models.

## Features

- **Image Editing**: Generate images based on text prompts and reference image styles
  - Qwen Image Edit Plus (synchronous)
  - Wanxiang 2.5 Image Edit (asynchronous)
- **Video Generation**: Create videos from images with synchronized audio
  - Wanxiang 2.5 Image-to-Video
- **Advanced Parameters**: 
  - Negative prompts
  - Seed control for reproducibility
  - Multiple image generation (1-6)
  - Video resolution (480P/720P/1080P)
  - Video duration (5s/10s)
  - Auto audio generation
- **Automatic Image Padding**: Ensures images meet minimum dimension requirements (384x384)
- **Network Resilience**: Built-in retry logic and proxy support

## Tech Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript
- **APIs**: Alibaba Cloud DashScope (Qwen & Wanxiang models)
- **Image Processing**: Pillow (PIL)
- **HTTP**: Requests with retry logic

## Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/xiwu0904/qwen-test.git
   cd qwen-test
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure API key**
   ```bash
   cp .env.example .env
   # Edit .env and add your DASHSCOPE_API_KEY
   ```

5. **Run the server**
   ```bash
   python server.py
   ```

6. **Access the application**
   ```
   Open http://localhost:8080 in your browser
   ```

## Environment Variables

Create a `.env` file with the following:

```env
DASHSCOPE_API_KEY=your_api_key_here

# Optional: Proxy settings
# HTTP_PROXY=http://your-proxy:port
# HTTPS_PROXY=http://your-proxy:port
```

## API Models

- **Qwen Image Edit Plus** (`qwen-image-edit-plus-2025-10-30`)
  - Synchronous image editing and enhancement
  
- **Wanxiang 2.5 Image Edit** (`wan2.5-i2i-preview`)
  - Asynchronous multi-image fusion and editing
  
- **Wanxiang 2.5 Image-to-Video** (`wan2.5-i2v-preview`)
  - Generate videos from images with audio

## Usage

1. **Upload an image** - Select a reference image (JPG, PNG)
2. **Choose model** - Select between image editing or video generation
3. **Enter prompt** - Describe what you want to generate
4. **Set parameters** - Configure advanced options (optional)
5. **Generate** - Click generate and wait for results

### Tips for Reproducibility

- Use the same seed value for consistent results
- Disable "Prompt Extend" when using seed for exact reproduction
- Note that AI prompt optimization may introduce variations

## Project Structure

```
.
├── server.py              # Flask backend server
├── index.html            # Web interface
├── config.py             # Configuration and model definitions
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── test_connection.py   # Network diagnostic tool
├── setup.sh            # Setup script
└── .gitignore          # Git ignore rules
```

## Network Troubleshooting

If you encounter connection issues:

1. **Run diagnostic tool**
   ```bash
   python test_connection.py
   ```

2. **Configure proxy** (if needed)
   ```bash
   export HTTP_PROXY=http://your-proxy:port
   export HTTPS_PROXY=http://your-proxy:port
   ```

3. **Check retry settings** in `config.py`:
   - `MAX_RETRIES = 3`
   - `RETRY_DELAY = 2`
   - `TIMEOUT = 120`

## API Documentation

- [Qwen Image Edit API](https://help.aliyun.com/zh/model-studio/qwen-image-edit-api)
- [Wanxiang Image Edit API](https://help.aliyun.com/zh/model-studio/wan2-5-image-edit-api-reference)
- [Wanxiang Image-to-Video API](https://help.aliyun.com/zh/model-studio/image-to-video-api-reference)

## License

MIT
