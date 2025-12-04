from prisma import Prisma
import asyncio
import bcrypt

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def reset_admin_password():
    db = Prisma()
    await db.connect()

    # Find admin user
    user = await db.user.find_unique(
        where={"email": "admin@dygsom.pe"}
    )

    if not user:
        print("❌ User admin@dygsom.pe not found")
        await db.disconnect()
        return

    # Set new password
    new_password = "SecurePass123"
    password_hash = hash_password(new_password)

    # Update user
    await db.user.update(
        where={"id": user.id},
        data={"password_hash": password_hash}
    )

    print(f"✅ Password reset successful for {user.email}")
    print(f"   New password: {new_password}")

    await db.disconnect()

asyncio.run(reset_admin_password())
