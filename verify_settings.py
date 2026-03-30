#!/usr/bin/env python3
"""
Script to verify that environment variables and settings are loaded correctly
"""

import os
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_environment_variables():
    """Check if environment variables are properly set"""
    print("Checking environment variables...")

    # Check if .env file exists
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"+ .env file found at: {env_file}")

        # Read and display LLM_API_KEY presence (but not the actual value for security)
        with open(env_file, "r") as f:
            env_content = f.read()
            has_api_key = (
                "LLM_API_KEY=" in env_content
                and len(env_content.split("LLM_API_KEY=")[1].split("\n")[0].strip()) > 0
            )
            if has_api_key:
                print("+ LLM_API_KEY is present in .env file")
            else:
                print("- LLM_API_KEY is NOT present in .env file")
    else:
        print("- .env file not found")

    # Check what's currently in the environment
    api_key = os.getenv("LLM_API_KEY")
    if api_key and len(api_key) > 0:
        print(f"+ LLM_API_KEY is set in environment (length: {len(api_key)})")
    else:
        print("- LLM_API_KEY is NOT set in environment")


def verify_settings_loading():
    """Test that settings are loaded correctly"""
    print("\nTesting settings loading...")

    try:
        # Test the API settings
        from api.config.settings import settings as api_settings

        print(f"+ API Settings loaded successfully")
        print(
            f"  - LLM_API_KEY length: {len(api_settings.LLM_API_KEY) if api_settings.LLM_API_KEY else 0}"
        )
        print(f"  - LLM_API_URL: {api_settings.LLM_API_URL}")
        print(f"  - LLM_MODEL: {api_settings.LLM_MODEL}")
        print(f"  - API_HOST: {api_settings.API_HOST}")
        print(f"  - DEBUG: {api_settings.DEBUG}")

        if api_settings.LLM_API_KEY:
            print("  [OK] API key is properly loaded in API settings")
        else:
            print("  [FAIL] API key is NOT loaded in API settings")

    except Exception as e:
        print(f"✗ Failed to load API settings: {e}")

    try:
        # Test the main config settings
        from config.settings import settings as main_settings

        print(f"\n+ Main Settings loaded successfully")
        print(
            f"  - LLM_API_KEY length: {len(main_settings.LLM_API_KEY) if main_settings.LLM_API_KEY else 0}"
        )
        print(f"  - LLM_API_URL: {main_settings.LLM_API_URL}")

        if main_settings.LLM_API_KEY:
            print("  [OK] API key is properly loaded in main settings")
        else:
            print("  [FAIL] API key is NOT loaded in main settings")

    except Exception as e:
        print(f"✗ Failed to load main settings: {e}")


def test_llm_service():
    """Test that LLM service can access the API key"""
    print("\nTesting LLM service initialization...")

    try:
        from api.llm_service import AlibabaLLMService

        llm_service = AlibabaLLMService()
        print(f"+ LLM Service initialized successfully")
        print(f"  - API key loaded: {'Yes' if llm_service.api_key else 'No'}")
        print(f"  - Model: {llm_service.model}")
        print(f"  - Base URL: {llm_service.base_url}")

        if llm_service.api_key:
            print("  [OK] LLM service has access to API key")
        else:
            print("  [FAIL] LLM service does NOT have access to API key")

    except Exception as e:
        print(f"[FAIL] Failed to initialize LLM service: {e}")


def main():
    print("CGGI RAG System - Settings Verification")
    print("=" * 60)

    verify_environment_variables()
    verify_settings_loading()
    test_llm_service()

    print("\n" + "=" * 60)
    print("Settings verification completed!")


if __name__ == "__main__":
    main()
