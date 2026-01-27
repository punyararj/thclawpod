#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""
Simple test client for Clawdpod.

Usage:
    uv run test_client.py [--server URL] [--speaker NAME]
"""

import argparse
import httpx

def main():
    parser = argparse.ArgumentParser(description="Test Clawdpod server")
    parser.add_argument("--server", default="http://localhost:7001", help="Server URL")
    parser.add_argument("--speaker", default="Test", help="Speaker name")
    parser.add_argument("--token", default=None, help="Auth token")
    args = parser.parse_args()

    headers = {"Content-Type": "application/json"}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"

    print(f"🦞 Clawdpod Test Client")
    print(f"   Server: {args.server}")
    print(f"   Speaker: {args.speaker}")
    print(f"   Say 'quit' or 'goodbye' to exit\n")

    while True:
        try:
            text = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not text:
            continue
        if text.lower() in ("quit", "exit", "q"):
            print("Bye!")
            break

        try:
            response = httpx.post(
                f"{args.server}/chat",
                json={"text": text, "speaker": args.speaker},
                headers=headers,
                timeout=90.0,
            )
            response.raise_for_status()
            data = response.json()
            
            print(f"Dobby: {data['reply']}")
            
            if data.get("end_conversation"):
                print("\n[Conversation ended]")
                break
                
        except httpx.HTTPError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Error: {e}")

        print()

if __name__ == "__main__":
    main()
