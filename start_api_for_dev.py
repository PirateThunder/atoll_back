import asyncio

import uvicorn


async def start_api():
    uvicorn.run('atoll_back.api.asgi:app', reload=True, workers=1, port=8080, host='127.0.0.1')

    
if __name__ == '__main__':
    asyncio.run(start_api())
