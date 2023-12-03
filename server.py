from fastapi import FastAPI
from fastapi_socketio import SocketManager
from loguru import logger
from starlette.responses import FileResponse
from starlette.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="./public"), name="static")
socket_manager = SocketManager(app=app, mount_location="/ws")

# Словарь для хранения статуса подключения пользователей
connected_users = {}

ice_servers = [
    {
        "urls": "stun:stun.relay.metered.ca:80",
    },
    {
        "urls": "turn:a.relay.metered.ca:80",
        "username": "a5438070f98de1786441a350",
        "credential": "G7x6io6w9wcc/AU6",
    },
    {
        "urls": "turn:a.relay.metered.ca:80?transport=tcp",
        "username": "a5438070f98de1786441a350",
        "credential": "G7x6io6w9wcc/AU6",
    },
    {
        "urls": "turn:a.relay.metered.ca:443",
        "username": "a5438070f98de1786441a350",
        "credential": "G7x6io6w9wcc/AU6",
    },
    {
        "urls": "turn:a.relay.metered.ca:443?transport=tcp",
        "username": "a5438070f98de1786441a350",
        "credential": "G7x6io6w9wcc/AU6",
    },
]

@app.sio.on("connect")
async def connect(sid, environ):
    """Обработка подключения нового пользователя."""
    connected_users[sid] = {"connected": True}
    await app.sio.emit("update-user-list", {"userIds": list(connected_users.keys())})
    await app.sio.emit("iceServers", ice_servers, room=sid)  # Отправляем серверы ICE новому пользователю
    logger.info(f"User {sid} connected")


@app.sio.on("disconnect")
async def disconnect(sid):
    """Обработка отключения пользователя."""
    connected_users.pop(sid, None)
    await app.sio.emit("update-user-list", {"userIds": list(connected_users.keys())})
    logger.info(f"User {sid} disconnected")


@app.sio.on("requestUserList")
async def request_user_list(sid):
    """Отправка обновленного списка пользователей."""
    await app.sio.emit("update-user-list", {"userIds": list(connected_users.keys())})
    logger.info(f"{sid} requested user list update")


@app.sio.on("mediaOffer")
async def media_offer(sid, data):
    """Обработка предложения для общения."""
    await app.sio.emit(
        "mediaOffer", {"from": data["from"], "offer": data["offer"]}, room=data["to"]
    )
    logger.info(f"Media Offer from {data['from']}")


@app.sio.on("mediaAnswer")
async def media_answer(sid, data):
    """Обработка ответа на предложение об общении."""
    await app.sio.emit(
        "mediaAnswer", {"from": data["from"], "answer": data["answer"]}, room=data["to"]
    )
    logger.info(f"Media Answer from {data['from']}")


@app.sio.on("iceCandidate")
async def ice_candidate(sid, data):
    """Обработка ICE Candidate."""
    await app.sio.emit(
        "remotePeerIceCandidate", {"candidate": data["candidate"]}, room=data["to"]
    )
    logger.info(f"Ice candidate for  {data['to']}")


@app.get("/")
def read_root():
    """Отображение главной страницы."""
    return FileResponse("./public/index.html")