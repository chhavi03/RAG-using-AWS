import boto3
import json

REGION = "us-east-1"

print("=" * 60)
print(f"Testing Bedrock in region: {REGION}")
print("=" * 60)

runtime = boto3.client("bedrock-runtime", region_name=REGION)

# --- Test 1: InvokeModel (current approach) ---
print("\n[1] Testing InvokeModel (Titan Embed v2)...")
try:
    response = runtime.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": "hello world"})
    )
    print("   [OK] InvokeModel WORKS!")
except Exception as e:
    print(f"   [FAIL] InvokeModel failed: {e}")

# --- Test 2: Converse API (Nova Lite LLM) ---
print("\n[2] Testing Converse API (Nova Lite)...")
try:
    response = runtime.converse(
        modelId="amazon.nova-lite-v1:0",
        messages=[{"role": "user", "content": [{"text": "Say hello"}]}]
    )
    text = response["output"]["message"]["content"][0]["text"]
    print(f"   [OK] Converse WORKS! Response: {text[:60]}")
except Exception as e:
    print(f"   [FAIL] Converse failed: {e}")

# --- Test 3: Try us-west-2 region ---
print("\n[3] Testing InvokeModel in us-west-2...")
try:
    r2 = boto3.client("bedrock-runtime", region_name="us-west-2")
    response = r2.invoke_model(
        modelId="amazon.titan-embed-text-v2:0",
        body=json.dumps({"inputText": "hello world"})
    )
    print("   [OK] us-west-2 InvokeModel WORKS!")
except Exception as e:
    print(f"   [FAIL] us-west-2 failed: {e}")

# --- Test 4: InvokeModel with older Titan v1 ---
print("\n[4] Testing InvokeModel (Titan Embed v1 - older model)...")
try:
    response = runtime.invoke_model(
        modelId="amazon.titan-embed-text-v1",
        body=json.dumps({"inputText": "hello world"})
    )
    print("   [OK] Titan v1 WORKS!")
except Exception as e:
    print(f"   [FAIL] Titan v1 failed: {e}")

print("\n" + "=" * 60)