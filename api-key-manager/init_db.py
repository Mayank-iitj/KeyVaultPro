"""
Database Initialization Script
Designed & Engineered by Mayank Sharma
https://mayyanks.app
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import inspect
from app.database.connection import engine, Base
from app.database.models import (
    User, APIKey, AuditLog, UsageStats, RefreshToken,
    RateLimitBucket, WebhookEvent, AnomalyDetection
)


async def init_database():
    """Initialize database with all tables"""
    print("🔄 Initializing database...")
    print(f"📁 Database URL: {engine.url}")
    
    async with engine.begin() as conn:
        # Check existing tables
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()
        
        existing_tables = await conn.run_sync(get_tables)
        
        if existing_tables:
            print(f"\n📊 Existing tables found: {', '.join(existing_tables)}")
            print("\n⚠️  Database already initialized!")
            
            # Show table counts
            from sqlalchemy import text
            for table in existing_tables:
                result = await conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   • {table}: {count} records")
        else:
            print("\n🆕 No tables found. Creating schema...")
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            print("\n✅ Database schema created successfully!")
            print("\n📋 Tables created:")
            print("   • users - User accounts with RBAC")
            print("   • refresh_tokens - JWT refresh tokens")
            print("   • api_keys - API key management")
            print("   • audit_logs - Comprehensive audit trail")
            print("   • usage_stats - Usage statistics")
            print("   • rate_limit_buckets - Rate limiting")
            print("   • webhook_events - Webhook handling")
            print("   • anomaly_detections - Security monitoring")
    
    print("\n🎉 Database ready for use!")


async def check_database_health():
    """Verify database connectivity and structure"""
    print("\n🔍 Running database health check...")
    
    async with engine.begin() as conn:
        from sqlalchemy import text
        
        # Test basic query
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
        print("   ✅ Database connection OK")
        
        # Check all tables exist
        required_tables = [
            'users', 'api_keys', 'audit_logs', 'usage_stats',
            'refresh_tokens', 'rate_limit_buckets', 'webhook_events',
            'anomaly_detections'
        ]
        
        def get_tables(connection):
            inspector = inspect(connection)
            return inspector.get_table_names()
        
        existing_tables = await conn.run_sync(get_tables)
        
        for table in required_tables:
            if table in existing_tables:
                print(f"   ✅ Table '{table}' exists")
            else:
                print(f"   ❌ Table '{table}' missing!")
                return False
    
    print("\n✅ Database health check passed!")
    return True


async def reset_database():
    """Drop all tables and recreate (USE WITH CAUTION!)"""
    print("\n⚠️  WARNING: This will DELETE ALL DATA!")
    
    # Require explicit confirmation
    import os
    if os.getenv("CONFIRM_RESET") != "yes":
        print("❌ Reset cancelled. Set CONFIRM_RESET=yes to proceed.")
        return
    
    print("🔄 Dropping all tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("   ✅ All tables dropped")
        
        await conn.run_sync(Base.metadata.create_all)
        print("   ✅ Tables recreated")
    
    print("\n✅ Database reset complete!")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database management utility")
    parser.add_argument(
        "command",
        choices=["init", "check", "reset"],
        help="Command to execute"
    )
    
    args = parser.parse_args()
    
    try:
        if args.command == "init":
            await init_database()
            await check_database_health()
        elif args.command == "check":
            await check_database_health()
        elif args.command == "reset":
            await reset_database()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
