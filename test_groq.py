import sys
import traceback
from restaurant_rec.phase3.settings import GroqSettings
from restaurant_rec.phase3.groq_client import chat_completion

def run_tests():
    settings = GroqSettings.from_env()
    if not settings.api_key:
        print("FAIL: No API key found in settings after loading .env")
        sys.exit(1)
    
    print("Test 1: Check basic connectivity and response")
    try:
        response = chat_completion(
            system_prompt="You are a helpful assistant. Reply with only the word 'PONG'.",
            user_content="PING",
            settings=settings
        )
        print(f"Response: '{response}'")
        if "PONG" in response.upper():
            print("Test 1 Passed: Received expected response.\n")
        else:
            print("Test 1 Failed: Unexpected response.\n")
    except Exception as e:
        print(f"Test 1 Failed with exception: {e}")
        traceback.print_exc()

    print("Test 2: Check JSON output format")
    try:
        response = chat_completion(
            system_prompt="You are a helpful assistant. Output valid JSON only without any markdown formatting block like ```json.",
            user_content="Give me a JSON object with a single key 'status' and value 'ok'.",
            settings=settings
        )
        print(f"Response: '{response}'")
        import json
        data = json.loads(response)
        if data.get("status") == "ok":
            print("Test 2 Passed: JSON parsed correctly.\n")
        else:
            print("Test 2 Failed: JSON structure incorrect.\n")
    except Exception as e:
        print(f"Test 2 Failed with exception: {e}")
        traceback.print_exc()

    print("Test 3: Check invalid model handling")
    try:
        bad_settings = GroqSettings(
            api_key=settings.api_key,
            model="invalid-model-name-xyz",
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            timeout_seconds=settings.timeout_seconds,
            recommendation_top_k=settings.recommendation_top_k,
        )
        response = chat_completion(
            system_prompt="Test",
            user_content="Test",
            settings=bad_settings
        )
        print("Test 3 Failed: Expected an error but got a response.\n")
    except Exception as e:
        print(f"Test 3 Passed: Got expected exception for invalid model: {e}\n")
        
if __name__ == "__main__":
    run_tests()
