import requests
import json






#Organise the extracted data into a dictionary:

#We start by the Category Article, with all its data and object properties
def ArticleMapper(r_json):
    Article={}
    Article['title']= r_json['title']
    Article['DOI']= r_json['doi']
    Article['publication_date']= r_json['publication_date']
    Article['CitationCount'] =r_json['cited_by_count']
    Article['referencedWorksCount']=r_json['referenced_works_count']
    Article['Cites']= r_json['referenced_works']
    Article['abstract_inverted_index']= r_json['abstract_inverted_index']


    Article['Keyword']=[]
    for k in r_json['keywords']:
        Article['Keyword'].append(k['id'])


    Article['authors_id']=[]
    for l in r_json['authorships']:
        Article['authors_id'].append(l['author']['id'])

    '''
        author_dict['name']=l['author']['display_name']
        author_dict['orcid']=l['author']['orcid']
    '''
    Article['PublishedIn']={'type':r_json['primary_location']['source']['type'],
                            'id':r_json['primary_location']['source']['id']}
    
    return Article



    




# article de conference: https://doi.org/10.1609/aaai.v35i1.16089
DOI_list=["https://doi.org/10.1109/ACCESS.2024.3498107"]

'''
         "https://doi.org/10.1016/j.jobe.2024.111150",
         "https://doi.org/10.48550/ARXIV.2408.00540",
          "https://doi.org/10.1109/ACCESS.2024.3498107" 
'''

urlBase="https://api.openalex.org/works/"
headers= {"Authorization": f"apikey token=8vD5VvhPAxO0BMfmjGEIm8"}

with requests.Session() as s:
    s.headers= headers

    for d in DOI_list:
        r=s.get(url=urlBase+d)

        if r.status_code==200:
            with open('OpenAlexResponseALL', 'a') as f:
                r_json=r.json()
                json.dump(r.json(),f,  indent=4)
                f.write("================Next DOI ==========================")
        else:
            print('There is a problem with doi', d)


Article= ArticleMapper(r_json)


with open('Article', 'w') as f:
    json.dump(Article,f, indent=4)

#Now we pass to Category Author,

def Author_Mapper(r_auth_json):      

    Author={}
    Author['FullName']= r_auth_json['display_name']
    Author['orcid']= r_auth_json['orcid']
    Author['works_count']= r_auth_json['works_count']
    Author['institutions']=[]
    
    for i in r_auth_json['affiliations']:
        institutions_dict={}
        institutions_dict['Name']=i['institution']['display_name']
        institutions_dict['Country']=i['institution']['country_code']
        institutions_dict['type']=i['institution']['type']
    
    Author['institutions'].append(institutions_dict)

    return Author

with requests.Session() as s:
    s.headers= headers
    urlBaseAuthor="https://api.openalex.org/authors/"

    A=[]
    for auth in Article['authors_id']:
        url= auth

        u=url.split("/")[-1:][0]
        #print(u)

        new_url= urlBaseAuthor + u

        r=s.get(url=new_url)
        #print(r.json())

        r_auth_json = r.json()
        Author=Author_Mapper(r_auth_json)
        A.append(Author)


#Tere is a problem here, 

with open('Author_data2', 'w') as f:
    f.write(str(A))


#Now we mapp journal data
with requests.Session() as s:
    s.headers= headers
    urlBaseAuthor="https://api.openalex.org/"


    source=  Article['PublishedIn']['id']
    u= source.split("/")[-1:][0]

    new_url= urlBaseAuthor + u

    r=s.get(url=new_url)
        #print(r.json())

    r_source_json = r.json()
    #print(r_source_json)


def Source_Mapper(r_source_json):
    Source={}
    Source['Name']=r_source_json['display_name']
    Source['Type']=r_source_json['type']
    Source['host_organization']=r_source_json['host_organization_name']
    Source['Country']= r_source_json['country_code']
    #source['Field']=[]
    L=[]

    for f in r_source_json['topics']:
        L.append(f['display_name'])
    Source['Field']=L

    return Source
    


Source= Source_Mapper(r_source_json)

with open('SourceJournalConference', 'w') as f:
    json.dump(Source,f, indent=4)












 





#print(Article)

            


