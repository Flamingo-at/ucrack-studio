import asyncio
import aiohttp

from re import findall
from imbox import Imbox
from random import choice
from loguru import logger
from aiohttp import ClientSession
from string import digits, ascii_letters
from pyuseragents import random as random_useragent


def get_imap(provider: str, login: str, password: str):
    return Imbox(
        provider,
        username=login,
        password=password,
        ssl=True,
        ssl_context=None,
        starttls=None)


async def get_token_email(email: str, password: str):
    imbox = get_imap('outlook.office365.com', email, password)
    return(await recv_message(imbox))


async def recv_message(imbox: Imbox):
    folder = "Inbox"
    for _, message in imbox.messages(folder=folder)[::-1]:
        if message.sent_from[0]["email"] == "no-reply@ucrackstudio.com":
            return findall(r'"https:\/\/ucrackstudio.com\/register\/(.+)"', message.body["plain"][0])[0].split('"')[0]
    return(await recv_message(imbox))


async def sending_captcha(client: ClientSession):
    try:
        response = await client.get(f'http://api.captcha.guru/in.php?key={user_key}&method=userrecaptcha \
            &googlekey=6LezJBAjAAAAAMn-H25FUbbmvUR7WX8P-2JAWELC&pageurl=https://ucrackstudio.com/&softguru=129939')
        data = await response.text()
        if 'ERROR' in data:
            logger.error(data)
            await asyncio.sleep(1)
            return(await sending_captcha(client))
        id = data[3:]
        return(await solving_captcha(client, id))
    except:
        raise Exception()


async def solving_captcha(client: ClientSession, id: str):
    for i in range(100):
        try:
            response = await client.get(f'http://api.captcha.guru/res.php?key={user_key}&action=get&id={id}')
            data = await response.text()
            if 'ERROR' in data:
                logger.error(data)
                return(await sending_captcha(client))
            elif 'OK' in data:
                return(data[3:])
            return(await solving_captcha(client, id))
        except:
            raise Exception()
    return(await sending_captcha(client))


async def register(client: ClientSession, email: str, password: str, token: str):
    try:
        response = await client.post('https://api.orca.ucrackstudio.com/request-handler/accounts/signUpWithEmail',
                                     json={
                                         "email": email,
                                         "password": password,
                                         'verificationToken': token,
                                         "displayName": email.split('@')[0],
                                         "language": 'EN',
                                         "captchaToken": await sending_captcha(client)
                                     })
        (await response.json())['userId']
    except:
        raise Exception()


async def worker(q: asyncio.Queue):
    while True:
        try:
            async with aiohttp.ClientSession(
                headers={'user-agent': random_useragent()}
            ) as client:

                emails = await q.get()
                email, password_email = emails.split(":")

                logger.info('Send email')
                await client.post('https://api.orca.ucrackstudio.com/request-handler/accounts/sendEmailVerificationToken',
                                  json={
                                      'email': email,
                                      'language': 'EN'
                                  })

                logger.info('Get token')
                token = await get_token_email(email, password_email)

                password = ''.join(
                    [choice(digits + ascii_letters + '!#$%&*+-=?@^_') for _ in range(15)])

                logger.info('Registration')
                await register(client, email, password, token)
        except:
            with open('error.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{password_email}\n')
            logger.error('Error\n')
        else:
            with open('registered.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{password}\n')
            logger.success('Successfully\n')

        await asyncio.sleep(delay)


async def main():
    emails = open("emails.txt", "r+").read().strip().split("\n")

    q = asyncio.Queue()

    for account in list(emails):
        q.put_nowait(account)

    tasks = [asyncio.create_task(worker(q)) for _ in range(threads)]
    await asyncio.gather(*tasks)

    
if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("Bot UCrack Studio register @flamingoat\n")

    user_key = input('Captcha key: ')
    delay = int(input('Delay(sec): '))
    threads = int(input('Threads: '))

    asyncio.run(main())