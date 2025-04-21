# GameUploader.py
import os, time, pathlib, json, requests

print('启动上传服务')

# 默认配置
default_config = {
    'ImgPath': str(pathlib.Path.home()) + '\\Documents\\Escape from Tarkov\\Screenshots\\',
    'sleeptime': 1,
    'playerid': 'default_player',
    'roomid': 'default_room',
    'server': 'http://localhost:5000'
}

def check_or_create_config():
    config_path = 'setting.json'
    if not os.path.exists(config_path) or os.path.getsize(config_path) == 0:
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        print('setting.json 文件不存在或为空，已创建默认配置。请修改后重新运行。')
        exit()

    try:
        with open(config_path, 'r') as f:
            cfg = json.load(f)
        return cfg
    except json.JSONDecodeError:
        print('setting.json 格式错误，已重置为默认配置。请修改后重新运行。')
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=4)
        exit()

# 加载配置
cfg = check_or_create_config()
ImgPath = cfg['ImgPath']
sleeptime = cfg['sleeptime']
playerid = cfg['playerid']
roomid = cfg['roomid']
server = cfg['server']

last_uploaded = ''

def getPosition():
    global last_uploaded
    dir = os.listdir(ImgPath)
    if not dir:
        return None
    newest = dir[0]
    if newest == last_uploaded:
        return None
    last_uploaded = newest
    os.remove(os.path.join(ImgPath, newest))
    return newest

while True:
    time.sleep(sleeptime)
    fname = getPosition()
    if fname:
        try:
            res = requests.post(server + "/upload", json={
                'player': playerid,
                'room': roomid,
                'filename': fname
            })
            print(f"上传成功: {fname}")
        except Exception as e:
            print("上传失败:", e)
