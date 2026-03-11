import asyncio
import os
import sys

# Add backend to path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from services.memory_service import memory_service
from db.database import engine, Base
from sqlalchemy import text

async def main():
    print("🔄 Initializing connection to database...")
    async with engine.begin() as conn:
        print("Ensuring vector extension exists...")
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        print("Creating ALL Tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Database tables ready.")
        
    print("\n🧠 Testing Mem0 (Layer 1 Memory) - Warning: Requires OpenAI API Key in .env!")
    
    if memory_service.mem0:
        print("Adding sample memory...")
        memory_service.add_conversation_memory(
            user_id="test_user", 
            message="I struggle to start working in the mornings, usually procrastinating on Reddit.",
            context="Morning Check-in"
        )
        
        print("Searching for relevant context...")
        results = memory_service.search_relevant_context(user_id="test_user", query="procrastination context")
        
        if results:
            print(f"✅ Search successful. Found {len(results)} results.")
            for r in results:
                print(f"   - Match: {r}")
        else:
            print("⚠️ Search returned empty. Is your OpenAI key valid?")
    else:
        print("❌ Mem0 is not initialized. Make sure OPENAI_API_KEY is in your .env file.")

if __name__ == "__main__":
    asyncio.run(main())
