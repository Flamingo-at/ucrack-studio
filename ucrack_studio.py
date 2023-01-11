import asyncio
import aiohttp

from re import findall
from random import choice
from loguru import logger
from aiohttp import ClientSession
from pyuseragents import random as random_useragent
from string import digits, ascii_letters, punctuation


async def sending_captcha(client: ClientSession):
    try:
        response = await client.get(f'http://api.captcha.guru/in.php?key={user_key}&method=userrecaptcha \
            &googlekey=6LezJBAjAAAAAMn-H25FUbbmvUR7WX8P-2JAWELC&pageurl=https://ucrackstudio.com/')
        data = await response.text()
        if 'ERROR' in data:
            logger.error(print(data))
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
                logger.error(print(data))
                raise Exception()
            elif 'OK' in data:
                return(data[3:])
            return(await solving_captcha(client, id))
        except:
            raise Exception()
    raise Exception()


async def create_email(client: ClientSession):
    try:
        response = await client.get("https://www.1secmail.com/api/v1/?action=genRandomMailbox&count=1")
        email = (await response.json())[0]
        return email
    except Exception:
        logger.error("Failed to create email")
        await asyncio.sleep(1)
        return await create_email(client)


async def check_email(client: ClientSession, login: str, domain: str, count: int):
    try:
        response = await client.get('https://www.1secmail.com/api/v1/?action=getMessages&'
                                    f'login={login}&domain={domain}')
        email_id = (await response.json())[0]['id']
        return(email_id)
    except:
        while count < 30:
            count += 1
            await asyncio.sleep(1)
            return await check_email(client, login, domain, count)
        logger.error('Emails not found')
        raise Exception()


async def get_token(client: ClientSession, login: str, domain: str, email_id):
    try:
        response = await client.get('https://www.1secmail.com/api/v1/?action=readMessage&'
                                    f'login={login}&domain={domain}&id={email_id}')
        data = (await response.json())['body']
        token = findall(
            r'"https:\/\/ucrackstudio.com\/register\/(.+)"', data)[0]
        return(token)
    except:
        logger.error('Failed to get token')
        raise Exception()


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


async def worker():
    while True:
        try:
            async with aiohttp.ClientSession(
                headers={'user-agent': random_useragent()}
            ) as client:

                logger.info('Get email')
                email = await create_email(client)

                logger.info('Send email')
                await client.post('https://api.orca.ucrackstudio.com/request-handler/accounts/sendEmailVerificationToken',
                                  json={
                                      'email': email,
                                      'language': 'EN'
                                  })

                logger.info('Check email')
                email_id = await check_email(client, email.split('@')[0], email.split('@')[1], 0)

                logger.info('Get token')
                token = await get_token(client, email.split('@')[0], email.split('@')[1], email_id)

                password = ''.join(
                    [choice(digits + ascii_letters + '!#$%&*+-=?@^_') for _ in range(15)])

                logger.info('Registration')
                await register(client, email, password, token)
        except:
            logger.error('Error\n')
        else:
            logger.info('Saving data')
            with open('registered.txt', 'a', encoding='utf-8') as file:
                file.write(f'{email}:{password}\n')
            logger.success('Successfully\n')

        await asyncio.sleep(delay)


async def main():
    tasks = [asyncio.create_task(worker()) for _ in range(threads)]
    await asyncio.gather(*tasks)

    
if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    print("Bot UCrack Studio register @flamingoat\n")

    user_key = input('Captcha key: ')
    delay = int(input('Delay(sec): '))
    threads = int(input('Threads: '))

    asyncio.run(main())