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
minimum_rap_for_webhook = config['information']['minimum_win_for_webhook']

trade_mode = config['trade_information']['type']
sort_by = config['trade_information']['sort']

my_minimum = config['trade_information']['my_offer']['minimum_items']
their_minimum = config['trade_information']['their_offer']['minimum_items']
decline_projected = config['trade_information']['my_offer']['decline_projected']
keep_giving_projected = config['trade_information']['their_offer']['decline_projected']

blacklisted_traders = config['trade_information']['blacklisted_users']
blacklisted_giving = config['trade_information']['my_offer']['blacklisted_items']
blacklisted_receiving = config['trade_information']['their_offer']['blacklisted_items']

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

def check(inbounds):
    global good, bad, blacklisted, skipped
    for trade in inbounds:
        dont = open('checked.txt','r').read()
        try:
            me, them, decline, me_proj = 0, 0, False, False
            while True:
                if not str(trade) in dont:
                    r = req.get(f'https://trades.roblox.com/v1/trades/{trade}').json()
                    if 'userAssets' in str(r):
                        me_hook = []
                        them_hook = []
                        themvalues_hook = []
                        mevalues_hook = []
                        uaid = str(r['offers'][1]['user']['id'])

                        for i in range(len(r['offers'][0]['userAssets'])):
                            id = str(r['offers'][0]['userAssets'][i]['assetId'])
                            current, name, proj = values[id].split('/',3)
                            me += int(current)
                            crn = "{:,}".format(int(current))
                            me_hook.append(f'**Item**: {name}\n**Value**: {crn}\n')
                            if int(id) in blacklisted_giving:
                                decline = True
                            if keep_giving_projected == False:
                                if str(proj) == '1':
                                    me_proj = True
                        myrobux = r['offers'][0]['robux']
                        me_hook.append(f'**Robux**: {myrobux}\n')

                        for i in range(len(r['offers'][1]['userAssets'])):
                            id = str(r['offers'][1]['userAssets'][i]['assetId'])
                            current, name, proj = values[id].split('/',3)
                            them += int(current)
                            crn = "{:,}".format(int(current))
                            them_hook.append(f'**Item**: {name}\n**Value**: {crn}\n')
                            if int(id) in blacklisted_receiving:
                                decline = True
                            if decline_projected == True:
                                if str(proj) == '1':
                                    decline = True
                        theirrobux = r['offers'][1]['robux']
                        them_hook.append(f'**Robux**: {theirrobux}\n')

                        if len(r['offers'][1]['userAssets']) < their_minimum:
                            decline = True
                        if len(r['offers'][0]['userAssets']) < my_minimum:
                            decline = True
                        if uaid in blacklisted_traders:
                            decline = True
                        if keep_giving_projected == True:
                            if me >= them and me_proj == False:
                                decline = True
                        elif keep_giving_projected == False:
                            if me >= them:
                                decline = True

                        if decline == True:
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
                            with open('checked.txt','a') as p:
                                p.writelines(f'{trade}\n')
                            break

                        elif decline == False:
                            me_hook = '\n'.join(me_hook)
                            them_hook = '\n'.join(them_hook)

                            profit = int(them) - int(me)
                            percentage = (1 - int(me) / int(them)) * 100
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
                                        'color': int('880808',16),
                                        'fields': [
                                            {'name': f'📤 Giving [{me}]','value': f'{me_hook}','inline':True},
                                            {'name': f'\u200b','value': f'\u200b','inline':True},
                                            {'name': f'📥 Receiving Items: [{them}]','value': f'{them_hook}','inline':True},
                                            {'name': '💸 Profit','value': f'{profit} ({percentage}%)','inline':False},
                                            ]
                                        }]
                                    }
                                if int(them - me) >= minimum_rap_for_webhook:
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


Thread(target=title).start()

values = rolimons()
inbounds = scrape_trades()

if sort_by == 'ascending':
    inbounds = inbounds[::-1]
    check(inbounds)
elif sort_by == 'descending':
    check(inbounds)
