#!/bin/bash

# Setup script for Qwen Image Generation Web App

echo "🚀 Setting up Qwen Image Generation Web App..."

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file and add your DASHSCOPE_API_KEY"
    echo "   You can get your API key from: https://bailian.console.aliyun.com/"
else
    echo "✅ .env file already exists"
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment is not activated"
    echo "   Please run: source venv/bin/activate"
    exit 1
fi

echo ""
echo "✨ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "   1. Edit .env file and add your DASHSCOPE_API_KEY"
echo "   2. Run: python server.py"
echo "   3. Open http://localhost:5000 in your browser"
echo ""
