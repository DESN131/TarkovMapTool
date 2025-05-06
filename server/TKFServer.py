# TKFServer.py
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

game_data = {}  # { room_id: { player_id: { 'filename': ..., 'last_updated': ..., 'color': ..., 'style': ... } } }

PLAYER_COLORS = ['#6aff00', '#f9ff01', '#00f6ff', '#ff00d0', '#ff7f0e']

@app.route('/upload', methods=['POST'])
def upload():
    data = request.get_json()
    room = data['room']
    player = data['player']
    fname = data['filename']

    if room not in game_data:
        game_data[room] = {}

    if player not in game_data[room]:
        color = PLAYER_COLORS[len(game_data[room]) % len(PLAYER_COLORS)]
    else:
        color = game_data[room][player]['color']
    game_data[room][player] = {
        'filename': fname,
        'last_updated': datetime.now(),
        'color': color
    }
    print(game_data)
    return jsonify({'status': 'ok'})

@app.route('/state/<room_id>', methods=['GET'])
def state(room_id):
    players = game_data.get(room_id, {})
    now = datetime.now()
    expired_players = []
    client_ip = request.remote_addr

    # Automatically delete expired players (3 minutes)
    for p, data in players.items(): 
        if now - data['last_updated'] > timedelta(minutes=3):
            expired_players.append(p)

    for p in expired_players:
        print(f"delete expired players {p}")
        del players[p]

    result = {
        "client_ip": client_ip,
        "players": {
            p: {
                "filename": data["filename"],
                "color": data["color"]
            } for p, data in players.items()
        }
    }
    
    # return jsonify({
    #         p: {
    #         'filename': data['filename'],
    #         'color': data['color']
    #         } for p, data in players.items()})

    return jsonify(result)

app.run(host='0.0.0.0', port=5000)
