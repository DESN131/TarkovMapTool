# TKFServer.py
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os, json, time
import logging

USE_REDIS = os.getenv("USE_REDIS", "1") == "1"
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Flask(__name__)

# 将 Flask 的 logger 交给 gunicorn.error（它会输出到 --error-logfile 指定的位置；你已设为 "-" 即 stderr）
gunicorn_error_logger = logging.getLogger("gunicorn.error")
if gunicorn_error_logger.handlers:
    app.logger.handlers = gunicorn_error_logger.handlers
    app.logger.setLevel(gunicorn_error_logger.level)
else:
    # 保险：若非 gunicorn 环境，也确保能打印到 stdout/stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
    app.logger.setLevel(logging.INFO)

if USE_REDIS:
    import redis
    r = redis.Redis.from_url(REDIS_URL)
    EXPIRE_SECONDS = 180  # 3 min

    PLAYER_COLORS = ['#6aff00', '#f9ff01', '#00f6ff', '#ff00d0', '#ff7f0e']
    def room_key(room): return f"room:{room}"

    @app.route('/upload', methods=['POST'])
    def upload():
        data = request.get_json()
        player = data['player']
        app.logger.info(f"Player upload: {player}")
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
        expired = []

        for p_b, data_b in room_players.items():
            p = p_b.decode()
            d = json.loads(data_b.decode())
            if now - d.get('last_updated', 0) <= EXPIRE_SECONDS:
                result[p] = {'filename': d['filename'], 'color': d['color']}
            else:
                expired.append(p)
                r.hdel(key, p)

        if result:
            r.expire(key, EXPIRE_SECONDS)

        # —— 日志部分 —— #
        # 记录被清理的玩家（如有）
        for p in expired:
            app.logger.info(f"[STATE] room={room_id} worker={os.getpid()} expired_player={p}")

        # 记录当前活跃玩家
        active_players = sorted(result.keys())
        # 如果担心过长，可以只打前 N 个
        N = 50
        shown_players = active_players[:N]
        more = len(active_players) - len(shown_players)
        tail = f" (+{more} more)" if more > 0 else ""
        app.logger.info(
            f"[STATE] room={room_id} worker={os.getpid()} active_count={len(active_players)} "
            f"active_players={','.join(shown_players)}{tail}"
        )
        # —— 日志结束 —— #

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
