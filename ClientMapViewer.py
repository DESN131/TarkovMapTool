from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import requests
import time
import os
import json
import traceback
import pathlib

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
roomid = cfg['roomid']
playerid = cfg['playerid']
server = cfg['server']

def getAllPlayers():
    try:
        response = requests.get(f"{server}/state/{roomid}")
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}

def getInputBox(driver):
    return WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Paste file name here"]'))
    )

def openInputBox(driver):
    try:
        print("尝试点击 'Where am I?' 按钮以打开输入框")
        btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Where am i?")]'))
        )
        btn.click()
        print("已点击按钮，等待输入框出现")
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder="Paste file name here"]'))
        )
        print("输入框已显示")
    except Exception as e:
        print(f"打开输入框失败: {e}")
        exit()

def getMarker(driver: webdriver.Edge):
    marker = driver.find_element(By.XPATH, "//*[@class='marker']")
    return marker.get_attribute('style').rstrip("visibility: hidden;") + ";"

def setMarker(driver: webdriver.Edge, id, ps='', color='#f9ff01'):
    if not id:
        id = 'offline'
    try:
        driver.find_element(By.XPATH, f"//*[@id='{id}']")
    except:
        js = f'''var map=document.querySelector("#map");
            map.insertAdjacentHTML("beforeend","<div id='{id}' class='marker' style='{ps}width:6px;height:6px;border-radius:50%;background:{color};'></div>");'''
        driver.execute_script(js)
        return
    if ps == '':
        js = f'''var marker=document.querySelector("#{id}"); marker.remove();'''
    else:
        js = f'''var marker=document.querySelector("#{id}"); marker.setAttribute('style','{ps}background:{color};');'''
    driver.execute_script(js)

def wait_and_get_marker_style(driver):
    WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.XPATH, "//*[@class='marker']"))
    )
    marker = driver.find_element(By.XPATH, "/html/body/div/div/div/div[2]/div/div/div[4]/div")
    driver.execute_script('arguments[0].style.visibility="hidden";', marker)
    style = getMarker(driver)
    if not style.strip().startswith("left:") or "top:" not in style:
        raise Exception(f"marker style 无效: {style}")
    return style

if __name__ == "__main__":
    try:
        driver = webdriver.Edge(service=EdgeService(EdgeChromiumDriverManager().install()))
    except Exception as e:
        print(f"无法启动 Edge WebDriver: {e}")
        exit()

    driver.get('https://tarkov-market.com/maps/streets')
    time.sleep(3)
    openInputBox(driver)

    playerList = []

    while True:
        try:
            time.sleep(sleeptime)

            all_players = getAllPlayers()

            # 移除离开的玩家
            for p in list(playerList):
                if p not in all_players:
                    setMarker(driver, p, '')  # 清除 marker

            playerList = list(all_players.keys())

            for pid, info in all_players.items():
                fname = info['filename']
                color = info.get('color', '#f9ff01')

                try:
                    print(f"\n正在处理玩家: {pid}, 文件名: {fname}, 颜色: {color}")
                    input_box = getInputBox(driver)
                    # input_box.click()
                    # input_box.clear()
                    # input_box.send_keys(fname)
                    
                    driver.execute_script("""
                        let input = arguments[0];
                        let value = arguments[1];
                        input.value = value;
                        input.dispatchEvent(new Event('input', { bubbles: true }));
                        input.dispatchEvent(new Event('change', { bubbles: true }));
                    """, input_box, fname)

                    # print(f"已输入文件名: {fname}")

                    ps = wait_and_get_marker_style(driver)
                    # print(f"获取到 marker 样式: {ps}")

                    setMarker(driver, pid, ps, color)
                    print(f"成功绘制玩家: {pid}")

                except Exception as e:
                    print(f"绘制玩家 {pid} 失败: {e}")
        
        except Exception:
            print(traceback.format_exc())

        print('------------------------------------------------------')
