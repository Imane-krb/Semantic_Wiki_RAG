import requests
import json


username='EmaneKharroube@TestMediaWiki'
password='7mjt92063nk01nckcioj5b5acfkrgkqu.'

username2='EmaneKharroube'
password2='TestMediaWiki@7mjt92063nk01nckcioj5b5acfkrgkqu'

urlBase= "https://test.wikipedia.org/w/rest.php"

data= {'username': username,
          'password':password}



url1="https://test.wikipedia.org/w/rest.php"

headers ={'user-agent': 'MyWikiBot/1.0 (kharroube.imane@gmail.com)'}

#asking for login token
with requests.Session() as s:
    s.headers = headers 
    params={'action': 'query',
            'meta': 'tokens',
            'type': 'login',
            'format': 'json'}
    
    r1= s.get(url=url1, params=params)
    logintoken=r1.json()
    print(r1.json())


#Post request with credentials
    data={'action': 'login',
             
             'lgname': username2,
             'lgpassword': password2,
             'lgtoken': logintoken,
             'format': 'json'
             }
    
    r2=s.post(url= url1, data=data)
    #print(r2.json())


    #Get a CSRF token — query action=query&meta=tokens&type=csrf
    params3={'action': 'query',
             'meta':'tokens',
             'type': 'csrf',
             'format': 'json'
             }
    r3= s.get(url=url1, params=params3)
    crsftoken=r3.json()['query']['tokens']['csrftoken']
    #print(crsftoken)
'''
with requests.Session() as s:
    r1= s.get(url=urlBase, data=data)
    r1.raise_for_status()
    # Le cookie est conservé et renvoyé automatiquement à la prochaine requête
'''