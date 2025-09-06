# TKFServer.py
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os, json, time

USE_REDIS = os.getenv("USE_REDIS", "1") == "1"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Flask(__name__)

if USE_REDIS:
    import redis
    r = redis.Redis.from_url(REDIS_URL)
    EXPIRE_SECONDS = 180  # 3 min

    PLAYER_COLORS = ['#6aff00', '#f9ff01', '#00f6ff', '#ff00d0', '#ff7f0e']
    def room_key(room): return f"room:{room}"

    @app.route('/upload', methods=['POST'])
    def upload():
        data = request.get_json()
        room = data['room']; player = data['player']; fname = data['filename']
        key = room_key(room)
        room_players = r.hgetall(key)

        if player.encode() in room_players:
            old = json.loads(room_players[player.encode()].decode())
            color = old.get('color', PLAYER_COLORS[0])
        else:
            color = PLAYER_COLORS[len(room_players) % len(PLAYER_COLORS)]

        payload = {'filename': fname, 'color': color, 'last_updated': int(time.time())}
        r.hset(key, player, json.dumps(payload))
        r.expire(key, EXPIRE_SECONDS)
        return jsonify({'status': 'ok'})

    @app.route('/state/<room_id>', methods=['GET'])
    def state(room_id):
        key = room_key(room_id)
        room_players = r.hgetall(key)
        now = int(time.time())
        result = {}
        for p_b, data_b in room_players.items():
            p = p_b.decode()
            d = json.loads(data_b.decode())
            if now - d.get('last_updated', 0) <= EXPIRE_SECONDS:
                result[p] = {'filename': d['filename'], 'color': d['color']}
            else:
                r.hdel(key, p)
        if result:
            r.expire(key, EXPIRE_SECONDS)
        return jsonify(result)
else:
    # 纯内存后备（开发/应急）
    game_data = {}
    PLAYER_COLORS = ['#6aff00', '#f9ff01', '#00f6ff', '#ff00d0', '#ff7f0e']

    @app.route('/upload', methods=['POST'])
    def upload_mem():
        data = request.get_json()
        room = data['room']; player = data['player']; fname = data['filename']
        room_map = game_data.setdefault(room, {})
        color = room_map.get(player, {}).get('color',
                    PLAYER_COLORS[len(room_map) % len(PLAYER_COLORS)])
        room_map[player] = {'filename': fname, 'last_updated': datetime.now(), 'color': color}
        return jsonify({'status': 'ok'})

    @app.route('/state/<room_id>', methods=['GET'])
    def state_mem(room_id):
        players = game_data.get(room_id, {})
        now = datetime.now()
        for p in [p for p, d in players.items() if now - d['last_updated'] > timedelta(minutes=3)]:
            del players[p]
        return jsonify({p: {'filename': d['filename'], 'color': d['color']} for p, d in players.items()})

# 健康检查
@app.route('/health', methods=['GET'])
def health():
    return jsonify({'ok': True})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=1688)
