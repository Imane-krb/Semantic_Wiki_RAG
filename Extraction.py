import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()
Authorisation= os.getenv("Authorisation")



#Get DOI link from referenced_works:




#Organise the extracted data into a dictionary:
#We start by the Category Article, with all its data and object properties
def ArticleMapper(r_json):
    Article={}
    Article['title']= r_json['title']
    Article['DOI']= r_json['doi']
    Article['publication_date']= r_json['publication_date']
    
    Article['referencedWorksCount']=r_json['referenced_works_count']
    Article['CitesArticles']= r_json['referenced_works']
    Article['abstract_inverted_index']= r_json['abstract_inverted_index']

    Article['CitesCount']=r_json['referenced_works_count']
    Article['CitedByCount'] =r_json['cited_by_count']

    Article['language']=r_json['language']
    Article['FWCI']=r_json['fwci']
    Article['topic']=r_json['primary_topic']['display_name']
    Article['Subfield']=r_json['primary_topic']['subfield']['display_name']
    Article['field']=r_json['primary_topic']['field']['display_name']



    Article['Keyword']=[]
    for k in r_json['keywords']:
        Article['Keyword'].append(k['display_name'])

    Article['authors_names']=[]
    Article['authors_id']=[]
    for l in r_json['authorships']:
        Article['authors_id'].append(l['author']['id'])
        Article['authors_names'].append(l['author']['display_name'])

    '''
        author_dict['name']=l['author']['display_name']
        author_dict['orcid']=l['author']['orcid']
    '''
    Article['PublishedIn']={'type':r_json['primary_location']['source']['type'],
                            'id':r_json['primary_location']['source']['id'],
                            'name':r_json['primary_location']['source']['display_name']}
    
    return Article



def Author_Mapper(r_auth_json):      

    Author={}
    Author['FullName']= r_auth_json['display_name']
    Author['orcid']= r_auth_json['orcid']
    Author['works_count']= r_auth_json['works_count']

    Author['h_index']=r_auth_json['summary_stats']['h_index']
    Author['i10_index']=r_auth_json['summary_stats']['i10_index']
    
    Author['institutions']=[]
    
    
    if r_auth_json['affiliations']:
        Author['Current institution']=r_auth_json['affiliations'][0]['institution']['display_name']
        for i in r_auth_json['affiliations']:
            institutions_dict={}
            institutions_dict['Name']=i['institution']['display_name']
            institutions_dict['Country']=i['institution']['country_code']
            institutions_dict['type']=i['institution']['type']
        
            Author['institutions'].append(institutions_dict)

    return Author

def Source_Mapper(r_source_json):
    Source={}
    Source['Name']=r_source_json['display_name']
    Source['Type']=r_source_json['type']
    Source['host_organization']=r_source_json['host_organization_name']
    Source['Country']= r_source_json['country_code']

    Source['ISSN']=r_source_json['issn'] #list
    Source['AlternateName']=r_source_json['alternate_titles']
    Source['is_in_doaj']=r_source_json['is_in_doaj']
    Source['h_index']=r_source_json['summary_stats']['h_index']
    Source['i10_index']=r_source_json['summary_stats']['i10_index']
    #source['Field']=[]
    L=[]

    for f in r_source_json['topics']:
        L.append(f['display_name'])
    Source['Field']=L

    return Source






def AbstractMapper(DOI):
    headers= {"Authorization": f"{Authorisation}"}
    urlBase="https://api.openalex.org/works/"
    urlBaseAuthor="https://api.openalex.org/authors/"
    urlBaseAuthor="https://api.openalex.org/"

    with requests.Session() as s:
        s.headers= headers
     
        r=s.get(url=urlBase+DOI)

#Getting the original response:
        if r.status_code==200:
            with open('DOI_OriginalResponse', 'a') as f:
                Doi_OriginalResponse=r.json()
                json.dump(Doi_OriginalResponse,f,  indent=4)
        else:
            print('There is a problem with doi', DOI)

#Mapping the original response to Article Category:
        Article= ArticleMapper(Doi_OriginalResponse)
        #print(Article['CitesArticles'])
        refsToInclude=[]
        for ref in Article['CitesArticles']:
            work_id=ref.split("/")[-1:][0]
            new_link= urlBaseAuthor + work_id
            r=s.get(url=new_link)
            if r.status_code==200:
                #print(r.json())
                if r.json()['doi']:
                    refsToInclude.append(r.json()['doi'])
        #print(refsToInclude)
        
        Article['CitesArticles']=refsToInclude
        
                

        with open('Article', 'w') as f:
            json.dump(Article,f, indent=4)


#Mapping the AuthorResponse to Author Category:
        AuthoreList=[] #List of dictionaries of every author
        for auth in Article['authors_id']:
            if auth:
                url= auth

                u=url.split("/")[-1:][0]
                #print(u)

                new_url= urlBaseAuthor + u

                r=s.get(url=new_url)
                #print(r.json())

                Author_OriginalResponse = r.json()

                #Troubleshoting:
                #print(r.json())
                #with open('Author_OriginalResponse', 'w') as f:
                    #json.dump(Author_OriginalResponse, f, indent=4)


                Author=Author_Mapper(Author_OriginalResponse)
                AuthoreList.append(Author)

        with open('ListOfAuthors', 'w') as f:
            f.write(str(AuthoreList))
        

#Mapping the SourceAnwser to Category JournlaConference

            source=  Article['PublishedIn']['id']
            u= source.split("/")[-1:][0]
            #print(u)

            new_url= urlBaseAuthor + u

            r=s.get(url=new_url)
                #print(r.json())

            Source_OriginalResponse = r.json()
            #print(r_source_json)

            with open('Source_OriginalResponse', 'w') as f:
                json.dump(Source_OriginalResponse, f, indent=4)
    
            
            Source= Source_Mapper(Source_OriginalResponse)

            with open('SourceJournalConference', 'w') as f:
                json.dump(Source,f, indent=4)
        
        return Article, AuthoreList, Source
    



        




# article de conference: https://doi.org/10.1609/aaai.v35i1.16089
DOI_list=["https://doi.org/10.48550/arXiv.2312.10997", "https://doi.org/10.1609/aaai.v35i1.16089"]




def MappedArticle(DOI):
    result= AbstractMapper(DOI)
    return result[0]

def MappedAuthorList(DOI):
    result= AbstractMapper(DOI)
    return result[1]

def MappedSource(DOI):
    result= AbstractMapper(DOI)
    return result[2]

#AbstractMapper(DOI_list[1])


#print(MappedArticle("https://doi.org/10.1109/ACCESS.2024.3498107"))

#print(MappedAuthorList("https://doi.org/10.1093/jamiaopen/ooaf067"))
'''
         "https://doi.org/10.1016/j.jobe.2024.111150",
         "https://doi.org/10.48550/ARXIV.2408.00540",
          "https://doi.org/10.1109/ACCESS.2024.3498107" 
'''





