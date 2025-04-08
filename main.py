import os
import sys
from dotenv import load_dotenv
load_dotenv()


def check_requirements():
    """Check if necessary components are set up before starting"""
    # Check if TELEGRAM_TOKEN is set
    if not os.getenv("TELEGRAM_TOKEN"):
        print("⚠️ TELEGRAM_TOKEN environment variable not set.")
        print("Please set it with:")
        print("  - Linux/Mac: export TELEGRAM_TOKEN='your_token_here'")
        print("  - Windows: set TELEGRAM_TOKEN=your_token_here")
        return False
    
    # Check if Ollama is likely running
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("localhost", 11434))
        s.close()
    except:
        print("⚠️ Ollama doesn't appear to be running on localhost:11434.")
        print("Please start Ollama with:")
        print("  ollama run gemma3:1b")
        return False
    
    return True

def setup_database():
    """Initialize the database and other components"""
    from db_setup import get_chroma_collection
    print("Setting up database...")
    collection = get_chroma_collection()
    print(f"✅ Database initialized with collection: {collection.name}")
    return True

def test_gemma():
    """Test if Gemma model is responding"""
    from gemma_integration import generate_text
    print("Testing connection to Gemma model...")
    try:
        response = generate_text("Hello, are you working?", max_tokens=10)
        print(f"✅ Gemma response: {response[:50]}...")
        return True
    except Exception as e:
        print(f"⚠️ Error connecting to Gemma model: {e}")
        print("Make sure Ollama is running with: ollama run gemma3:1b")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Starting Halsey - GemmaRAG Personal Assistant")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Setup checks failed. Please fix the issues above and try again.")
        sys.exit(1)
    
    if not setup_database():
        print("\n❌ Database setup failed.")
        sys.exit(1)
    
    if not test_gemma():
        print("\n❌ Gemma model test failed.")
        sys.exit(1)
    
    print("\n✅ All systems ready! Starting Telegram bot...\n")
    
    from telegram_bot import main
    main()