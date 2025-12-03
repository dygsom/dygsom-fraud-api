from prisma import Prisma
import asyncio

async def check_users():
    db = Prisma()
    await db.connect()

    users = await db.user.find_many()
    print(f'Total users in DB: {len(users)}')

    for user in users:
        print(f'  - {user.email} (role: {user.role})')

    await db.disconnect()

asyncio.run(check_users())
