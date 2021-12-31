import requests, colorama, ctypes, threading, re, json, time
from threading import Thread
from colorama import init
from colorama import Fore
req = requests.Session()
init()

cookie = input('Enter cookie: ')
req.cookies['.ROBLOSECURITY'] = cookie

trades = 0
good = 0
bad = 0

def title():
    while True:
        ctypes.windll.kernel32.SetConsoleTitleW(f'Trades Inbound: {trades} - Good Trades: {good} - Declined Trades: {bad}')

def rolimons():
    ids = []
    information = []
    r = requests.get('https://www.rolimons.com/deals').text
    items = re.findall('item_details = (.*?);', r)[0]
    total = json.loads(items)
    for x in total:
        info = total[x]
        if info[5] == None:
            name, use, projected, itemid = info[0], info[2], info[4], x
            ids.append(itemid)
            information.append(f'{use}/{name}/{projected}')
        elif info[5] != None:
            name, use, projected, itemid = info[0], info[5], info[4], x
            ids.append(itemid)
            information.append(f'{use}/{name}/{projected}')
    c = zip(ids, information)
    values = dict(c)
    return values

def scrape_trades():
    global trades
    cursor = ''
    tradeids = []
    while True:
        try:
            r = req.get(f'https://trades.roblox.com/v1/trades/inbound?cursor={cursor}&limit=100&sortOrder=Desc').json()
            if 'nextPageCursor' in str(r):
                cursor = r['nextPageCursor']
                if not cursor == None:
                    for i in range(len(r['data'])):
                        id = r['data'][i]['id']
                        tradeids.append(id)
                        trades += 1
                elif cursor == None:
                    for i in range(len(r['data'])):
                        id = r['data'][i]['id']
                        tradeids.append(id)
                        trades += 1
                    print(f'{Fore.LIGHTGREEN_EX}[+] Finished Scraping - {len(tradeids)} Trades Found')
                    return tradeids
            elif 'TooManyRequests' in str(r):
                print(f'{Fore.LIGHTYELLOW_EX}[-] Ratelimited - Waiting 1 minute')
                time.sleep(60)
                continue
        except Exception as err:
            print(f'{Fore.LIGHTBLACK_EX}[-] Exception - {err}')
            continue

def check(inbounds):
    global good, bad
    for trade in inbounds:
        try:
            me = 0
            them = 0
            projected = False
            while True:
                r = req.get(f'https://trades.roblox.com/v1/trades/{trade}').json()
                if 'userAssets' in str(r):
                    for i in range(len(r['offers'][0]['userAssets'])):
                        id = str(r['offers'][0]['userAssets'][i]['assetId'])
                        current, name, proj = values[id].split('/',3)
                        me += int(current)
                    for i in range(len(r['offers'][1]['userAssets'])):
                        id = str(r['offers'][1]['userAssets'][i]['assetId'])
                        current, name, proj = values[id].split('/',3)
                        them += int(current)
                        if proj == 1 or proj == '1':
                            projected = True
                        elif proj == None:
                            projected = False
                    if me >= them or projected == True:
                        while True:
                            r = req.post('https://auth.roblox.com/v1/logout')
                            csrf = r.headers['X-CSRF-TOKEN']
                            headers = {
                                'x-csrf-token': csrf
                                }
                            a = req.post(f'https://trades.roblox.com/v1/trades/{trade}/decline', headers=headers).text
                            if a == '{}':
                                print(f'{Fore.RED}[X] Trade Declined - {me} for {them}')
                                bad += 1
                                break
                            elif 'Declined' in a:
                                break
                            else:
                                print(f'{Fore.LIGHTYELLOW_EX}[-] Ratelimited - Waiting 1 minute')
                                time.sleep(60)
                                continue
                        break
                    elif them > me and projected == False:
                        good += 1
                        print(f'{Fore.LIGHTGREEN_EX}[+] Good Trade Found - {trade} - {me} for {them}')
                        break
                else:
                    print(f'{Fore.LIGHTYELLOW_EX}[-] Ratelimited - Waiting 1 minute')
                    time.sleep(60)
                    continue
            else:
                print(f'{Fore.LIGHTYELLOW_EX}[-] Ratelimited - Waiting 1 minute')
                time.sleep(60)
                continue
        except Exception as err:
            print(f'{Fore.LIGHTBLACK_EX}[-] Exception - {err}')
            continue


Thread(target=title).start()

values = rolimons()
inbounds = scrape_trades()

check(inbounds)
