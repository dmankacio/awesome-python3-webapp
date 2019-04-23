import asyncio, orms
from models import User

async def test(loop):
    await orms.create_pool(loop = loop, user='root', pwd='abc123', db='apw', host='heli.dman.me')
    u = User(name='test1', email='1231@dman.com', passwd='123456', image='about:blank')
    await u.save()

# 获取EventLoop:
loop = asyncio.get_event_loop()
# 执行coroutine
loop.run_until_complete(test(loop))
loop.close()




