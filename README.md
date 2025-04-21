# Escape from Tarkov 实时地图定位工具

本项目用于在 Escape from Tarkov 游戏中，基于截图文件名中的坐标信息，实现玩家位置的实时地图显示功能。支持多人联机地图同步，可视化追踪玩家位置，使用浏览器自动控制地图显示。

## 📌 功能特性

- 自动从游戏截图中解析坐标
- 实时上传坐标信息至服务器
- 客户端浏览器自动加载地图并绘制位置
- 支持多玩家同步显示及颜色区分
- 在地图中自动移除不活跃玩家

## 🧩 项目结构. 

├── server / TKFServer.py # 服务端，Flask 接收玩家上传信息并提供 state 接口
|
├── game_client / GameUploader.py # 游戏端，监听截图并上传截图文件名 
|
├── map_client / ClientMapViewer.py # 客户端，通过 Selenium 控制网页绘制所有玩家位置 
|
└── README.md # 项目说明文档

## 🚀 使用说明

### 1. 安装依赖

确保使用 Python 3.7+

进入所在的端的文件夹，然后安装依赖：

```bash
pip install -r requirements.txt
```

### 2. 配置文件

首次运行程序将自动生成 setting.json：

```
{
  "ImgPath": "C:\\Users\\你的用户名\\Documents\\Escape from Tarkov\\Screenshots\\",
  "sleeptime": 1,
  "playerid": "your_name",
  "roomid": "your_room",
  "server": "http://localhost:5000"
}
```

请根据你的实际情况修改，注意：

- 请先在游戏中进行截图，以生成Documents\Escape from Tarkov\Screenshots\ 文件夹
- playerid不能为纯数字，且不要与其他玩家重复
- 一同游玩的玩家请确保roomid一致，否则无法在地图中显示其他玩家的位置
- 将server改为服务器的ip:端口,端口默认为5000

修改完setting.json后再次运行程序，此时可以正常启动。

### 3. 启动服务端

在服务端：

```bash
cd server
python TKFServer.py
```

默认监听 5000 端口。

### 4. 启动截图监听上传端

在游戏端：

```bash
cd game_client
python GameUploader.py
```

在游戏中按截图键进行截图，程序会自动监测截图文件夹中新截图，并上传文件名信息到服务器。

截图键请自行在游戏设置中设置。


### 5. 启动客户端地图浏览器

在客户端：

```bash
cd map_client
python ClientMapViewer.py
```

自动打开 Tarkov Market 的地图页面，绘制所有玩家位置。
