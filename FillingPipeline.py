import requests 
import json
import os
import time
from dotenv import load_dotenv
from Extraction import AbstractMapper, MappedAuthorList, MappedArticle, MappedSource
from UndoInvertIndex import Undo_Invert_Index, maxIndex






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


def YesOrNo(a):
    if a:
        return 'Yes'
    return 'No'

def deletePage(crsftoken,s, title, urlBase):
    data={'action': 'delete',
            'title': title,
            'token': crsftoken,
            'format': 'json'
            }
    
    r4= s.post(url=urlBase, data=data)
    return (r4.json())

def Filling_Pipeline(DOI):

    KeywordList= MappedArticle(DOI)['Keyword']
    #print(KeywordList)

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




#Creating Keyword pages:
        print('=========Creating Keyword pages============')
        TraceabilityK=[]
        print('Creating Keyword Pages')
        for k in KeywordList:
            data5={'action': 'edit',
                    'title': k,
                    'text': f'{{{{keyword|name={k}}}}}',
                    'token': crsftoken,
                    'format': 'json'
                    }
                
            r3= s.post(url=urlBase, data=data5)
            if r3.status_code==200:
                TraceabilityK.append(k)
            else:
                print('the kyeword page creation has failed', r3.json())

            time.sleep(3)
            
            #TraceabilityK.append(r3.json()['edit']['title'])
        print('The keyword pages created are',TraceabilityK)



    #ConferenceField={','.join(Source["Field"])}
#Creating pages for the Category Conference/Journal
        print('=========Creating Source pages============')
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

                        |AlternateNames={','.join(Source['AlternateName'])}
                        |ISSN={','.join(Source['ISSN'])}
                        |is_in_doaj={YesOrNo(Source['is_in_doaj'])}
                        |h_index={Source['h_index']}
                        |i10_index={Source['i10_index']}

                        }}}}''',
                    'token': crsftoken,
                    'format': 'json'
                    }
            
            r_conf= s.post(url=urlBase, data=dataSource)
            print('the Source is a conference')
            if r_conf.status_code==200:
                TraceabilitySource.append(Source['Name'])
            else:
                print('Post request failed for the SourcePage ',r_conf.json())

            time.sleep(3)
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

                        |AlternateNames={','.join(Source['AlternateName'])}
                        |ISSN={','.join(Source['ISSN'])}
                        |is_in_doaj={YesOrNo(Source['is_in_doaj'])}
                        |h_index={Source['h_index']}
                        |i10_index={Source['i10_index']}

                        }}}}''',
                    'token': crsftoken,
                    'format': 'json'
                    }
            
            r_jrnl= s.post(url=urlBase, data=dataSource)
            print('Source is a journal')
            if r_jrnl.status_code==200:
                TraceabilitySource.append(Source['Name'])
            else:
                print('Post request failed for the sourcePage ',r_conf.json())
            #TraceabilitySource.append(r_jrnl['edit']['title'])
            #print(TraceabilitySource)
            time.sleep(3)
        print('The Source page created is:',TraceabilitySource)


#Creating the pages for institution Category:
        print('=========Creating Institution pages============')
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
                    print('There is an error with an institution', r_inst.json())
                #print(r_inst.status_code)
                #print(r_inst.json())
                time.sleep(3)
                
        print('Institution Pages created are',InstitutionsCreated)
                
#|Current affiliation={auth['Current institution']}
#Creating pages for Author Category:
        print('=========Creating Author pages============')
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
 

                        |h_index={auth['h_index']}
                        |i10_index= {auth['i10_index']}
                        
                        }}}} ''',
                    'token': crsftoken,
                    'format': 'json'
                    }
            r_auth=s.post(url=urlBase,data=dataAuthor)
            #print(r_auth.json())
            if r_auth.json()['edit']['result']!= 'Success':
                print('there is problem with this one',r_auth.json() )
            else:
                AuthorsCreated.append(auth["FullName"])
            #print(r_auth.status_code)
            #print(r_auth.json())
            time.sleep(3)
            
            
        print('Author pages created are:',AuthorsCreated)
            
#
#Creating Pages for Article category:
        print('=========Creating Article pages============')
        TraceabilityArticles=[]
        dataArticle= {'action':'edit',
                    'title':Article['title'] ,
                    'text': f'''{{{{Article
                    |Articletitle={Article['title']}
                    |PublicationDate={Article['publication_date']}

                    |ReferencesCount={Article['CitesCount']}
                    |CitedByCount={Article['CitedByCount']}

                    |DOI={Article['DOI']}
                    |PublishedIn={Article['PublishedIn']['name']}
                    |Abstract={Undo_Invert_Index(Article["abstract_inverted_index"])}
                    |Author= {','.join(Article['authors_names'])}
                    |Keyword={','.join(Article['Keyword'])}
                    |Language={Article['language']}
                    |FWCI={Article['FWCI']}
                    |Topic={Article['topic']}
                    |Subfield={Article['Subfield']}
                    |Field={Article['field']}
                    |Cites={','.join(Article['CitesArticles'])}



                    }}}}''',

                    'token': crsftoken,
                    'format': 'json',
                    }
        r_art=s.post(url=urlBase, data=dataArticle)
        if r_art.status_code == 200:
            TraceabilityArticles.append(Article['title'])
        else:
            print(r_art.json())


        print('Article page created is',TraceabilityArticles)


listDOI=[
"https://doi.org/10.1080/17512549.2022.2136240",
"https://doi.org/10.1016/J.JII.2024.100747",
"https://doi.org/10.3390/BUILDINGS12050544",
"https://doi.org/10.3390/APP13158814",
"https://doi.org/10.1016/J.APENERGY.2021.116601",
"https://doi.org/10.1109/ACCESS.2024.3498107",
"https://doi.org/10.1016/J.JOBE.2024.111150",
"https://doi.org/10.48550/ARXIV.2408.00540",
]


for DOI in listDOI[2:]:
    Filling_Pipeline(DOI)
    time.sleep(3)
    print('######Next DOI ######')





'''
        "title": "A Comprehensive Review of Digital Twin Technology in Building Energy Consumption Forecasting",
        "DOI": "https://doi.org/10.1109/access.2024.3498107",
        "publication_date": "2024-01-01",
        "CitationCount": 18,
        "referencedWorksCount": 160,
'''





    
