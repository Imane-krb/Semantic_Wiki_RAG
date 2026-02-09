import requests 
import json
import os
from dotenv import load_dotenv
from Extraction import AbstractMapper, MappedAuthorList, MappedArticle, MappedSource





load_dotenv()

username= os.getenv("username")
password=os.getenv("password")

username2=os.getenv("username2")
password2=os.getenv("password2")

urlBase=os.getenv('urlBase')

headers={
    'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'
}



DOI_list=["https://doi.org/10.1109/ACCESS.2024.3498107"]

#DOI de test:
DOI="https://doi.org/10.1109/ACCESS.2024.3498107"

KeywordList= MappedArticle(DOI)['Keyword']
#print(KeywordList)


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
    print(crsftoken)




#Now we create a page:
#Creating Keyword page using keyword template:
    Traceability=[]
    for k in KeywordList:
        data5={'action': 'edit',
                'title': k,
                'text': f'{{{{keyword|name={k}}}}}',
                'token': crsftoken,
                'format': 'json'
                }
            
        r3= s.post(url=urlBase, data=data5)
        print(r3.json())
        #Traceability.append(r3.json()['edit']['title'])
    #print(Traceability)

#Delete a page:
    data6={'action': 'delete',
            'title': 'Keyword test via api',
             'token': crsftoken,
             'format': 'json'
             }
    
    #r4= s.post(url=urlBase, data=data6)
    #print(r4.json())


    
