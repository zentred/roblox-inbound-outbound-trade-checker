import requests, colorama, ctypes, threading, re, json, time, os, json
from threading import Thread
from colorama import init
from colorama import Fore
req = requests.Session()
init()
os.system('cls')

with open("config.json", "r") as config:
    config = json.load(config)
with open('checked.txt', 'a') as f:
    f.close()

webhook = config['information']['webhook']
cookie = config['information']['cookie']
loop = config['information']['loop']

trade_mode = config['config']['info']['tradeType'] # outbound/inbound
sort_by = config['config']['info']['tradeSort'] # ascending/descending
minimum_value = config['config']['info']['minimumValue']
minimum_profit = config['config']['info']['minimumProfit']

my_minimum = config['config']['giving']['minimumItems']
their_minimum = config['config']['receiving']['minimumItems']
decline_projected = config['config']['giving']['declineProjected']
keep_giving_projected = config['config']['receiving']['declineProjected']

blacklisted_traders = config['config']['info']['blacklistedUsers']
blacklisted_giving = config['config']['giving']['declineItems']
blacklisted_receiving = config['config']['receiving']['declineItems']
selling_under_rap = config['config']['receiving']['declineSellingUnderRap']

req.cookies['.ROBLOSECURITY'] = cookie

trades, good, bad, skipped = 0, 0, 0, 0

def title():
    while True:
        ctypes.windll.kernel32.SetConsoleTitleW(f'Total Trades: {trades} | Good Trades: {good} | Declined Trades: {bad} | Trades Already Checked: {skipped}')

def rolimons():
    ids = []
    information = []
    r = requests.get('https://www.rolimons.com/deals').text
    items = re.findall('item_details = (.*?);', r)[0]
    total = json.loads(items)
    for x in total:
        info = total[x]
        if info[5] == None:
            name, use, projected, itemid, price = info[0], info[2], info[4], x, info[1]
            ids.append(itemid)
            information.append(f'{use}/{name}/{projected}/{price}/{use}')
        elif info[5] != None:
            name, use, projected, itemid, price, realrap = info[0], info[5], info[4], x, info[1], info[2]
            ids.append(itemid)
            information.append(f'{use}/{name}/{projected}/{price}/{realrap}')
    c = zip(ids, information)
    values = dict(c)
    return values

def scrape_trades():
    global trades
    cursor = ''
    tradeids = []
    while True:
        try:
            r = req.get(f'https://trades.roblox.com/v1/trades/{trade_mode}?cursor={cursor}&limit=100&sortOrder=Desc').json()
            if 'nextPageCursor' in str(r):
                cursor = r['nextPageCursor']
                if not cursor == None:
                    for i in range(len(r['data'])):
                        tradeids.append(r['data'][i]['id'])
                        trades += 1
                elif cursor == None:
                    for i in range(len(r['data'])):
                        tradeids.append(r['data'][i]['id'])
                        trades += 1
                    print(f'{Fore.LIGHTGREEN_EX}[+] Finished Scraping - {len(tradeids)} Trades Found')
                    return tradeids
            elif 'TooManyRequests' in str(r):
                print(f'{Fore.WHITE}[{Fore.YELLOW}-{Fore.WHITE}]{Fore.YELLOW} Ratelimited {Fore.WHITE}- {Fore.YELLOW}Waiting {Fore.WHITE}1 {Fore.YELLOW}minute')
                time.sleep(60)
                continue
        except Exception as err:
            print(f'{Fore.LIGHTBLACK_EX}[-] Exception - {err}')
            continue

def check_decline(my_length, their_length, receiving_userid, me, them, me_proj):
    decline = None
    if their_length < their_minimum: decline = True
    if my_length < my_minimum: decline = True
    if receiving_userid in blacklisted_traders: decline = True
    if me < minimum_value or them < minimum_value: decline = True
    if keep_giving_projected == True:
        if me >= them and me_proj == False:
            decline = True
    elif keep_giving_projected == False:
        if me >= them:
            decline = True
    if decline == True:
        return 1
    elif decline == None:
        return 0

def check(inbounds):
    global good, bad, blacklisted, skipped
    for trade in inbounds:
        dont = open('checked.txt','r').read()
        try:
            me, them, decline, me_proj = 0, 0, 0, False
            while True:
                if not str(trade) in dont:
                    r = req.get(f'https://trades.roblox.com/v1/trades/{trade}').json()
                    if 'userAssets' in str(r):
                        me_hook, them_hook, themvalues_hook, mevalues_hook = [], [], [], []

                        myrobux, theirrobux = r['offers'][0]['robux'], r['offers'][1]['robux']
                        me_hook.append(f'\u200b\n**Robux**: {myrobux}\n')
                        them_hook.append(f'\u200b\n**Robux**: {theirrobux}\n')

                        for i in range(len(r['offers'][0]['userAssets'])):
                            id = str(r['offers'][0]['userAssets'][i]['assetId'])
                            current, name, proj, pric, realrap = values[id].split('/',5)
                            me_hook.append(f'**Item**: {name}\n**Value**: {"{:,}".format(int(current))}\n')
                            me += int(current)

                            if int(id) in blacklisted_giving or keep_giving_projected == False:
                                decline += 1

                        for i in range(len(r['offers'][1]['userAssets'])):
                            id = str(r['offers'][1]['userAssets'][i]['assetId'])
                            current, name, proj, pric, realrap = values[id].split('/',5)
                            them_hook.append(f'**Item**: {name}\n**Value**: {"{:,}".format(int(current))}\n')
                            them += int(current)

                            if int(id) in blacklisted_receiving:
                                decline += 1
                            if decline_projected == True and str(proj) == '1':
                                decline += 1
                            if selling_under_rap == True:
                                if int(pric) < int(realrap):
                                    decline += 1

                        their_username = r['offers'][1]['user']['name']
                        their_id = r['offers'][1]['user']['id']

                        numb = check_decline(len(r['offers'][0]['userAssets']), len(r['offers'][1]['userAssets']), str(r['offers'][1]['user']['id']), me, them, me_proj)
                        decline += numb

                        me_hook, them_hook = '\n'.join(me_hook), '\n'.join(them_hook)
                        profit, percentage = int(them) - int(me), (1 - int(me) / int(them)) * 100
                        if profit < minimum_profit:
                            decline += 1

                        if decline >= 1:
                            while True:
                                r = req.post('https://auth.roblox.com/v1/logout')
                                csrf = r.headers['X-CSRF-TOKEN']
                                headers = {
                                    'x-csrf-token': csrf
                                    }
                                a = req.post(f'https://trades.roblox.com/v1/trades/{trade}/decline', headers=headers).text
                                if a == '{}':
                                    print(f'{Fore.WHITE}[{Fore.RED}x{Fore.WHITE}] {Fore.RED}Trade Declined {Fore.WHITE}- {Fore.RED}{me} {Fore.WHITE}for {Fore.RED}{them}')
                                    bad += 1
                                    break
                                elif 'Declined' in a:
                                    break
                                else:
                                    print(f'{Fore.WHITE}[{Fore.YELLOW}-{Fore.WHITE}]{Fore.YELLOW} Ratelimited {Fore.WHITE}- {Fore.YELLOW}Waiting {Fore.WHITE}1 {Fore.YELLOW}minute')
                                    time.sleep(60)
                                    continue
                            break

                        elif decline == 0:
                            if '.' in str(percentage):
                                if len(str(percentage).split('.')[1]) >= 3:
                                    percentage = round(percentage, 2)

                            if me_proj == True:
                                print(f'{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] {Fore.LIGHTGREEN_EX}Giving Projected Trade Found {Fore.WHITE}- {Fore.LIGHTGREEN_EX}{trade} {Fore.WHITE}- {Fore.LIGHTGREEN_EX}{me} {Fore.WHITE}for {Fore.LIGHTGREEN_EX}{them}')
                            elif me_proj == False:
                                print(f'{Fore.WHITE}[{Fore.LIGHTGREEN_EX}+{Fore.WHITE}] {Fore.LIGHTGREEN_EX}Good Trade Found {Fore.WHITE}- {Fore.LIGHTGREEN_EX}{trade} {Fore.WHITE}- {Fore.LIGHTGREEN_EX}{me} {Fore.WHITE}for {Fore.LIGHTGREEN_EX}{them}')
                            good += 1
                            if trade_mode == 'inbound':
                                data = {
                                  'embeds':[{
                                      'author': {
                                          'name': f'Trade from {their_username} (click for rolimons)\n\u200b',
                                          'url': f'https://www.rolimons.com/player/{str(their_id)}'
                                          },
                                      'color': int('00CCFF',16),
                                      'fields': [
                                          {'name': f'📤 Giving [{me}]','value': f'{me_hook}','inline':True},
                                          {'name': f'\u200b','value': f'\u200b','inline':True},
                                          {'name': f'📥 Receiving Items: [{them}]','value': f'{them_hook}','inline':True},
                                          {'name': '💸 Profit','value': f'{profit} ({percentage}%)','inline':False},
                                      ],
                                      'thumbnail': {
                                          'url': f'http://www.roblox.com/Thumbs/Avatar.ashx?x=200&y=200&Format=Png&username={their_username}',
                                          },
                                      'footer': {
                                          'text': f'Trade ID: {trade}'
                                      }
                                    }]
                                }
                                requests.post(webhook, json=data)
                            with open('checked.txt','a') as p:
                                p.writelines(f'{trade}\n')
                            break
                    else:
                        print(f'{Fore.WHITE}[{Fore.YELLOW}-{Fore.WHITE}]{Fore.YELLOW} Ratelimited {Fore.WHITE}- {Fore.YELLOW}Waiting {Fore.WHITE}1 {Fore.YELLOW}minute')
                        time.sleep(60)
                        continue
                else:
                    skipped += 1
                    break
            else:
                print(f'{Fore.WHITE}[{Fore.YELLOW}-{Fore.WHITE}]{Fore.YELLOW} Ratelimited {Fore.WHITE}- {Fore.YELLOW}Waiting {Fore.WHITE}1 {Fore.YELLOW}minute')
                time.sleep(60)
                continue
        except Exception as err:
            print(f'{Fore.LIGHTBLACK_EX}[-] Exception - {err}')
            continue
    return None

Thread(target=title).start()

if loop == True:
    while True:
        values = rolimons()
        inbounds = scrape_trades()
        if sort_by == 'ascending':
            inbounds = inbounds[::-1]
            check(inbounds)
        elif sort_by == 'descending':
            check(inbounds)
else:
    values = rolimons()
    inbounds = scrape_trades()
    if sort_by == 'ascending':
        inbounds = inbounds[::-1]
        check(inbounds)
    elif sort_by == 'descending':
        check(inbounds)
