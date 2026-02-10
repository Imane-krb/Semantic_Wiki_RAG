import requests 
import json
import os
from dotenv import load_dotenv
from Extraction import AbstractMapper, MappedAuthorList, MappedArticle, MappedSource





load_dotenv()

username= os.getenv("Wiki_username")
password=os.getenv("Wiki_password")

username2=os.getenv("Wiki_username2")
password2=os.getenv("Wiki_password2")

urlBase=os.getenv('Wiki_urlBase')



headers={
    'User-Agent': 'CoolBot/0.0 (https://example.org/coolbot/; coolbot@example.org) generic-library/0.0'
}



DOI_list=["https://doi.org/10.1109/ACCESS.2024.3498107"]

#DOI de test confernce: https://doi.org/10.1609/aaai.v35i1.16089
DOI="https://doi.org/10.1109/ACCESS.2024.3498107"
#DOI= "https://doi.org/10.1609/aaai.v35i1.16089"


KeywordList= MappedArticle(DOI)['Keyword']
print(KeywordList)

Source=MappedSource(DOI)
AuthorList=MappedAuthorList(DOI)
Article=MappedArticle(DOI)




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
    #print(r2.json()) 

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
#Creating Keyword page using keyword template:
    TraceabilityK=[]
    for k in KeywordList:
        data5={'action': 'edit',
                'title': k,
                'text': f'{{{{keyword|name={k}}}}}',
                'token': crsftoken,
                'format': 'json'
                }
            
        r3= s.post(url=urlBase, data=data5)
        print(r3.json())
        #TraceabilityK.append(r3.json()['edit']['title'])
    #print(TraceabilityK)

#Delete a page:
    data6={'action': 'delete',
            'title': 'Keyword test via api',
             'token': crsftoken,
             'format': 'json'
             }
    
    #r4= s.post(url=urlBase, data=data6)
    #print(r4.json())

#ConferenceField={','.join(Source["Field"])}
#Creating pages for the Category Conference/Journal
    TraceabilitySource=[]
    dataSource={}
    if Source['Type']== "conference":
        dataSource={'action': 'edit',
                'title': Source['Name'],
                'text': f'''{{{{Conference
                    |ConferenceName={Source["Name"]}
                    |ConferenceCountry={Source["Country"]}
                    |ConferenceField={','.join(Source["Field"])}
                    |ConferenceHostOrganisation={Source["host_organization"]}

                    }}}}''',
                'token': crsftoken,
                'format': 'json'
                }
        
        r_conf= s.post(url=urlBase, data=dataSource)
        print('Source is a conference')
        print(r_conf.status_code)
        print(r_conf.json())
        #TraceabilitySource.append(r_conf['edit']['title'])
        #print(TraceabilitySource)
    else: 

        #fields_wikitext = " ".join([f"[[Has field::{f}]]" for f in Source["Field"]])

        dataSource={'action': 'edit',
                'title': Source['Name'],
                'text': f'''{{{{Journal
                    |JournalName={Source["Name"]}
                    |JournalCountry={Source["Country"]}
                    |JournalFields={','.join(Source["Field"])}
                    |HostOrganisation={Source["host_organization"]}

                    }}}}''',
                'token': crsftoken,
                'format': 'json'
                }
        
        r_jrnl= s.post(url=urlBase, data=dataSource)
        print('Source is a journal')
        print(r_jrnl.status_code)
        print(r_jrnl.json())
        print(Source['Name'])
        #TraceabilitySource.append(r_jrnl['edit']['title'])
        #print(TraceabilitySource)


#Creating the pages for institution Category:
    InstitutionsCreated=[]
    for auth in AuthorList:
        for inst in auth['institutions']:
            dataInst= {'action': 'edit',
                       'title': inst['Name'],
                       'text': f'''{{{{Institution
                           |InstitutionName={inst['Name']}
                           |InstitutionCountry={inst['Country']}
                           |InstitutionType={inst['type']}
                       }}}}''',
                       'token': crsftoken,
                        'format': 'json'
                       }
            r_inst= s.post(url=urlBase, data=dataInst)
            if r_inst.status_code==200:
                InstitutionsCreated.append(inst['Name'])
            else:
                print('There is an error with an institution', inst)
            #print(r_inst.status_code)
            #print(r_inst.json())
            
    #print(InstitutionsCreated)
            

#Creating pages for Author Category:
    AuthorsCreated=[]
    for auth in AuthorList:
        res=  [auth['institutions'][i]['Name'] for i in range(len(auth['institutions']))]
        res=','.join(res)

        dataAuthor={'action': 'edit',
                'title': auth['FullName'],
                'text': f'''{{{{ Author
                    |FullName={auth["FullName"]}
                    |WorkCount={auth["works_count"]}
                    |orcid={auth['orcid']}
                    |institution={res}
                    
                    }}}} ''',
                'token': crsftoken,
                'format': 'json'
                }
        r_auth=s.post(url=urlBase,data=dataAuthor)

        if r_auth.json()['edit']['result']!= 'Success':
            print('there is problem with this one',r_auth.json() )
        else:
            AuthorsCreated.append(auth["FullName"])
        #print(r_auth.status_code)
        #print(r_auth.json())
        
        
    #print(AuthorsCreated)
        

#Creating Pages for Article category:
    dataArticle= {'action':'edit',
                  'title':Article['title'] ,
                 'text': f'''{{{{Article
                 |Articletitle={Article['title']}
                 |PublicationDate={Article['publication_date']}
                 |CitationCount={Article['CitationCount']}
                 |DOI={Article['DOI']}
                 |PublishedIn={Article['PublishedIn']['name']}
                 |Abstract={Article["abstract_inverted_index"]}
                 |Author= {','.join(Article['authors_names'])}
                 |Keyword={','.join(Article['Keyword'])}
                 |Cites= to add later



                 }}}}''',

                 'token': crsftoken,
                 'format': 'json',
                }
    #r_art=s.post(url=urlBase, data=dataArticle)
    #print(r_art.status_code)
    #print(r_art.json())

'''
    "title": "A Comprehensive Review of Digital Twin Technology in Building Energy Consumption Forecasting",
    "DOI": "https://doi.org/10.1109/access.2024.3498107",
    "publication_date": "2024-01-01",
    "CitationCount": 18,
    "referencedWorksCount": 160,

'''





    
