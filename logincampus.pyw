
import os, sys, time

import requests as rq
import socket

CAMPUS = ''
UNICOM = '%40unicom'
CMCC   = '%40cmcc'
TELECOM= '%40telecom'

# 获取本地ip
def get_default_gateway():
    def method1():
        if sys.platform != 'win32':
            try: 
                s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
                s.connect(('8.8.8.8',80)) 
                ip = s.getsockname()[0] 
            finally: 
                s.close() 
            print(ip)
            return ip
        if sys.platform == 'win32':
            return socket.gethostbyname(socket.gethostname())
    def method2():
        try:
            csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            csock.connect(('8.8.8.8', 80))
            (addr, port) = csock.getsockname()
            csock.close()
            return addr
        except socket.error:
            return "127.0.0.1"
    ret = method1()
    if ret[:3] != '10.': ret = method2()
    return ret

# 连接控制
def isconnected():
    url = 'http://edge.microsoft.com/captiveportal/generate_204'
    try:
        rq.get(url)
        return True
    except:
        return False

def islogined():
    url = 'http://edge.microsoft.com/captiveportal/generate_204'
    res = rq.get(url).status_code
    return res == 204

def login(user, passw, platform=UNICOM, *, wlan_user_ip=None , callback = 'dr1645959041575', wlan_user_mac='000000000000',wlan_ac_ip='', wlan_ac_name='', version='1645959030219'):
    # returns (result, msg)
    if wlan_user_ip is None:
        wlan_user_ip = get_default_gateway()
    url = f'http://10.2.5.251:801/eportal/?c=Portal&a=login&callback={callback}&login_method=1&user_account={user}{platform}&user_password={passw}&wlan_user_ip={wlan_user_ip}&wlan_user_mac={wlan_user_mac}&wlan_ac_ip={wlan_ac_ip}&wlan_ac_name={wlan_ac_name}&jsVersion=3.0&_={version}'
    resp = rq.get(url).text
    dct = eval(resp[resp.find('{') : -1])
    login.dct = dct
    return dct['result'] == '1'

# 发送消息
if sys.platform == 'win32':
    icon_path = './icon.ico'
    if not os.path.exists(icon_path): icon_path = None
    
    try:
        from win10toast import  ToastNotifier
        toaster = ToastNotifier()
        def toast(text, dur=10):
            toaster.show_toast('校园网登录器',text, duration=dur, icon_path=icon_path, threaded=True)
    except ImportError:
        def toast(text, dur=None):
            print(text)

def info(s, dur=10):
    if sys.platform == 'win32':
        # print(s)
        toast(s, dur)
    elif sys.platform == 'linux':
        appname = '校园网登录器'
        os.system(f'notify-send "{s}" -a {appname} -i ./icon.png')
    else:
        print(s)

def newfile(filename):
    content = '''* 这是校园网登录器的配置文件, 填写自己的信息就行。
账号\t\t= 10193***
密码\t\t= 26****
* 运营商可选 校园网、中国电信、中国移动、中国联通
运营商\t\t= 中国联通
* 下面的部分保持默认就行
联网时检测周期(s)\t= 15
断网时检测周期(s)\t= 5
'''
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)

def readfile(filename):
    res = dict()
    content = ''
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    for line in content.split('\n'):
        if '=' not in line: continue
        a,b = line.split('=')
        res[a.strip()] = b.strip()
    return res

def main():
    root = os.path.split(os.path.abspath(sys.argv[0]))[0]
    os.chdir(root)

    res = None
    user = None
    passw = None
    platform = None
    test_conn = None
    test_nconn = None
    try:
        res = readfile('setting.txt')
        user = res['账号']
        passw = res['密码']
        platform = res['运营商']
        if platform == '中国联通':
            platform = UNICOM
        elif platform == '中国电信':
            platform = TELECOM
        elif platform == '中国移动':
            platform = CMCC
        elif platform == '校园网':
            platform = CAMPUS
        else:
            raise ValueError(f'Invalid platform "{platform}"')
        test_conn = int(res['联网时检测周期(s)'])
        test_nconn = int(res['断网时检测周期(s)'])
    except:
        try:
            info('无法读取配置文件或者配置文件被损坏： "./setting.txt"')
            newfile('setting.txt')
            info('请在打开的窗口中填写配置文件并保存, 再重新打开软件。。。')
            if sys.platform == 'win32':
                os.startfile('setting.txt')
            else:
                os.system('gedit ./setting.txt')
            time.sleep(5)
        except:
            info('无法创建配置文件, 请检查软件权限。')
        return

    info('校园网登录2.0启动。')

    failcnt = 0
    while 1:
        try:
            if not islogined():
                if not login(user, passw, platform):
                    if failcnt == 1:
                        info('无法登录校园网, 可能是因为配置文件出错或者现在不是上网时段。')
                    failcnt += 1
                else:
                    info('成功登录校园网。')
                    failcnt = 0
                
                time.sleep(test_nconn)
            else:
                failcnt = 0
                time.sleep(test_conn)
        except Exception as esc:
            if type(Exception) is KeyboardInterrupt: raise esc

            info('网络断开。')
            while not isconnected():
                time.sleep(test_nconn)
            failcnt = 0
            info('网络重新连接。')

if __name__ == '__main__': main()
