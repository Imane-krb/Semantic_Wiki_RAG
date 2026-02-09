import requests 
import json

username='Admin@BotTestApi'
password= 'tpc928c848d00rgru3vqr0lh1u3rmb2r'

username2='Admin'
password2='BotTestApi@tpc928c848d00rgru3vqr0lh1u3rmb2r'

urlBase= "http://10.3.17.196:8080/api.php"

headers={
    'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'
}


with requests.Session() as s:
    s.headers= headers

#we ask for login token
    params={'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'}
    
    r1= s.get(url=urlBase, params=params)
    logintoken=r1.json()['query']['tokens']['logintoken']
    #print(logintoken)

#ze post the credentials:
    data={'action': 'login',
             
             'lgname': username,
             'lgpassword': password,
             'lgtoken': logintoken,
             'format': 'json'
             }
    
    r2=s.post(url= urlBase, data=data)
    #print(r2.json()) login with success

#we ask crsf token:
    params3={'action': 'query',
             'meta':'tokens',
             'type': 'csrf',
             'format': 'json'
             }
    r3= s.get(url=urlBase, params=params3)
    crsftoken=r3.json()['query']['tokens']['csrftoken']
    #print(crsftoken)

#Now we create a page:
    data4={'action': 'edit',
            'title': 'TestPage via action api',
             'text': 'the page creation was successful..llalalal',
             'token': crsftoken,
             'format': 'json'
             }
    
    r4= s.post(url=urlBase, data=data4)
    #print(r4.status_code)
    #print(r4.json())



#Creating Keyword page using keyword template:


    data5={'action': 'edit',
            'title': 'Keyword test via api',
             'text': '{{keyword|name=keywordTest via api2}}',
             'token': crsftoken,
             'format': 'json'
             }
    
    r3= s.post(url=urlBase, data=data5)
    print(r3.json())
    
