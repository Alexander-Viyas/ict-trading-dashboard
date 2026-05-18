from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.ws_manager import ws_manager
from app.services.mt5_bridge import mt5_bridge

router = APIRouter(prefix="/live", tags=["live"])


@router.websocket("/ws")
async def live_websocket(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Receive commands from frontend if needed
            data = await websocket.receive_text()
            # Echo back or handle commands
            await ws_manager.send_personal({"type": "echo", "message": data}, websocket)
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@router.get("/status")
async def live_status():
    return {
        "mt5_connected": mt5_bridge.connected,
        "active_ws_clients": len(ws_manager.active_connections),
        "buffers": {k: len(v) for k, v in mt5_bridge._candle_buffers.items()},
    }


@router.post("/mt5/connect")
async def connect_mt5():
    if not mt5_bridge.connected:
        await mt5_bridge.connect()
    return {"status": "connected", "mt5_connected": mt5_bridge.connected}


@router.post("/mt5/disconnect")
async def disconnect_mt5():
    await mt5_bridge.close()
    return {"status": "disconnected"}
