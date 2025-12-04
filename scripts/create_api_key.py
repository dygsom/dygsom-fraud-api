"""
CLI tool to create API keys.
Usage: python scripts/create_api_key.py --name "Client Name" --rate-limit 100
"""

import asyncio
import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from prisma import Prisma
from src.core.security import SecurityUtils
from src.repositories.api_key_repository import ApiKeyRepository


async def create_api_key(
    name: str,
    description: str = None,
    rate_limit: int = 100,
    expires_days: int = None,
    created_by: str = "cli"
):
    """Create API key and print it
    
    Args:
        name: Name for the API key
        description: Description of the key purpose
        rate_limit: Requests per minute (default: 100)
        expires_days: Days until expiration (default: None = never expires)
        created_by: User/system creating the key (default: "cli")
    """
    # Initialize Prisma
    prisma = Prisma()
    await prisma.connect()
    
    try:
        # Generate API key and hash
        plain_key, key_hash = SecurityUtils.generate_and_hash()
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create repository
        api_key_repo = ApiKeyRepository(prisma)
        
        # Create API key
        api_key_data = await api_key_repo.create_api_key(
            key_hash=key_hash,
            name=name,
            description=description,
            rate_limit=rate_limit,
            expires_at=expires_at,
            created_by=created_by
        )
        
        if not api_key_data:
            print("❌ Failed to create API key")
            return
        
        # Print success
        print("\n" + "="*60)
        print("✅ API Key Created Successfully")
        print("="*60)
        print(f"\n🔑 API Key: {plain_key}")
        print("\n⚠️  IMPORTANT: Save this key now! It will never be shown again.")
        print("\n📋 Key Details:")
        print(f"   ID:          {api_key_data.id}")
        print(f"   Name:        {api_key_data.name}")
        if api_key_data.description:
            print(f"   Description: {api_key_data.description}")
        print(f"   Rate Limit:  {api_key_data.rate_limit} req/min")
        if api_key_data.expires_at:
            print(f"   Expires At:  {api_key_data.expires_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        else:
            print(f"   Expires At:  Never")
        print(f"   Created By:  {api_key_data.created_by or 'N/A'}")
        print(f"   Created At:  {api_key_data.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print("\n💡 Usage Example:")
        print(f'   curl -H "X-API-Key: {plain_key}" http://localhost:8000/api/v1/fraud/score')
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"❌ Error creating API key: {e}")
        raise
    finally:
        await prisma.disconnect()


def main():
    """Parse arguments and create API key"""
    parser = argparse.ArgumentParser(
        description="Create a new API key for DYGSOM Fraud API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create basic API key
  python scripts/create_api_key.py --name "Production Client"
  
  # Create with custom rate limit
  python scripts/create_api_key.py --name "Test Client" --rate-limit 50
  
  # Create with expiration
  python scripts/create_api_key.py --name "Temporary Client" --expires-days 30
  
  # Create with all options
  python scripts/create_api_key.py \\
    --name "Partner API" \\
    --description "Partner integration for fraud detection" \\
    --rate-limit 200 \\
    --expires-days 365 \\
    --created-by "admin@dygsom.pe"
        """
    )
    
    parser.add_argument(
        "--name",
        required=True,
        help="Name for the API key (required)"
    )
    
    parser.add_argument(
        "--description",
        default=None,
        help="Description of the API key purpose"
    )
    
    parser.add_argument(
        "--rate-limit",
        type=int,
        default=100,
        help="Requests per minute (default: 100)"
    )
    
    parser.add_argument(
        "--expires-days",
        type=int,
        default=None,
        help="Days until expiration (default: never expires)"
    )
    
    parser.add_argument(
        "--created-by",
        default="cli",
        help="User/system creating the key (default: cli)"
    )
    
    args = parser.parse_args()
    
    # Validate rate limit
    if args.rate_limit < 1 or args.rate_limit > 10000:
        print("❌ Error: Rate limit must be between 1 and 10000")
        sys.exit(1)
    
    # Validate expires days
    if args.expires_days is not None and args.expires_days < 1:
        print("❌ Error: Expiration days must be at least 1")
        sys.exit(1)
    
    # Create API key
    asyncio.run(create_api_key(
        name=args.name,
        description=args.description,
        rate_limit=args.rate_limit,
        expires_days=args.expires_days,
        created_by=args.created_by
    ))


if __name__ == "__main__":
    main()
