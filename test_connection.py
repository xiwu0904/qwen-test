#!/usr/bin/env python3
"""
Network connection diagnostic script for Qwen API
"""

import sys
import socket
import requests
from dotenv import load_dotenv
import config

# Load environment variables
load_dotenv()

def test_dns_resolution():
    """Test DNS resolution for API endpoint"""
    print("\n1. Testing DNS resolution...")
    try:
        hostname = "dashscope.aliyuncs.com"
        ip_address = socket.gethostbyname(hostname)
        print(f"   ✅ DNS resolution successful: {hostname} -> {ip_address}")
        return True
    except socket.gaierror as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return False

def test_network_connectivity():
    """Test basic network connectivity"""
    print("\n2. Testing network connectivity...")
    try:
        # Test connection to a reliable host
        socket.create_connection(("www.google.com", 80), timeout=5)
        print("   ✅ Network connectivity OK (www.google.com reachable)")
        return True
    except (socket.timeout, socket.error) as e:
        print(f"   ❌ Network connectivity issue: {e}")
        return False

def test_api_endpoint():
    """Test connection to Qwen API endpoint"""
    print("\n3. Testing API endpoint connectivity...")
    try:
        hostname = "dashscope.aliyuncs.com"
        port = 443
        sock = socket.create_connection((hostname, port), timeout=10)
        sock.close()
        print(f"   ✅ Can connect to {hostname}:{port}")
        return True
    except (socket.timeout, socket.error) as e:
        print(f"   ❌ Cannot connect to API endpoint: {e}")
        return False

def test_https_request():
    """Test HTTPS request to API"""
    print("\n4. Testing HTTPS request to API...")
    try:
        # Get proxy settings
        proxies = config.get_proxies()
        if proxies:
            print(f"   Using proxy: {proxies}")
        
        response = requests.get(
            "https://dashscope.aliyuncs.com",
            timeout=10,
            proxies=proxies
        )
        print(f"   ✅ HTTPS request successful (status: {response.status_code})")
        return True
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error: {e}")
        print("   Suggestion: Check SSL certificate or try disabling SSL verification (not recommended for production)")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ Connection Error: {e}")
        return False
    except requests.exceptions.Timeout as e:
        print(f"   ❌ Timeout Error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False

def check_api_key():
    """Check if API key is configured"""
    print("\n5. Checking API key configuration...")
    if config.DASHSCOPE_API_KEY and config.DASHSCOPE_API_KEY != 'sk-your-api-key-here':
        print(f"   ✅ API key configured (starts with: {config.DASHSCOPE_API_KEY[:10]}...)")
        return True
    else:
        print("   ❌ API key not configured or using default value")
        print("   Please set DASHSCOPE_API_KEY in .env file")
        return False

def check_proxy_settings():
    """Check proxy configuration"""
    print("\n6. Checking proxy settings...")
    proxies = config.get_proxies()
    if proxies:
        print(f"   Proxy configured: {proxies}")
    else:
        print("   No proxy configured")
    return True

def main():
    print("=" * 60)
    print("Qwen API Connection Diagnostic Tool")
    print("=" * 60)
    
    results = []
    
    results.append(("DNS Resolution", test_dns_resolution()))
    results.append(("Network Connectivity", test_network_connectivity()))
    results.append(("API Endpoint", test_api_endpoint()))
    results.append(("HTTPS Request", test_https_request()))
    results.append(("API Key", check_api_key()))
    results.append(("Proxy Settings", check_proxy_settings()))
    
    print("\n" + "=" * 60)
    print("Diagnostic Summary")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    failed_tests = [name for name, result in results if not result]
    
    if failed_tests:
        print("\n" + "=" * 60)
        print("Troubleshooting Suggestions:")
        print("=" * 60)
        
        if "DNS Resolution" in failed_tests:
            print("\n• DNS Resolution failed:")
            print("  - Check your internet connection")
            print("  - Try changing DNS servers (e.g., 8.8.8.8, 1.1.1.1)")
            
        if "Network Connectivity" in failed_tests:
            print("\n• Network connectivity issue:")
            print("  - Check if you're connected to the internet")
            print("  - Check firewall settings")
            
        if "API Endpoint" in failed_tests or "HTTPS Request" in failed_tests:
            print("\n• Cannot reach API endpoint:")
            print("  - You might be behind a corporate firewall")
            print("  - Configure proxy in .env file:")
            print("    HTTP_PROXY=http://your-proxy:port")
            print("    HTTPS_PROXY=http://your-proxy:port")
            print("  - Try using a VPN if the service is geo-restricted")
            print("  - Check if antivirus/firewall is blocking the connection")
            
        if "API Key" in failed_tests:
            print("\n• API key not configured:")
            print("  - Edit .env file and set your DASHSCOPE_API_KEY")
            print("  - Get your API key from: https://bailian.console.aliyun.com/")
    else:
        print("\n✅ All diagnostic tests passed!")
        print("If you're still experiencing issues, the problem might be with the API request itself.")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
