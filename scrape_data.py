################################ Scrape the data and save the json file ##################################### 
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
import re
import time
import uuid
from ftfy import fix_text
import fitz  # PyMuPDF
import os
import json


### Get all herf links from main page and subpages
def get_all_links(main_link="https://www.mindgate.solutions"):
    first_hrefs=[]
    second_hrefs=[]
    pdf_links=[]
    headers = {'Accept-Encoding': 'identity'}
    r = requests.get(main_link, headers=headers)
    main_page_soup=BeautifulSoup(r.content, 'html.parser')
    count=0
    ### main page hrefs
    for a in main_page_soup.find_all('a', href=True):
        if a["href"] not in first_hrefs and bool(re.search("https://www.mindgate.solutions",a["href"])):
            if a["href"].endswith(".pdf"):
                pdf_links.append(a["href"])
            else:
                first_hrefs.append(a["href"])
                count+=1
                # print(count)

    count_sub=0
    ### Subpages hrefs
    for link in first_hrefs:
        r_sub = requests.get(link, headers=headers)
        sub_page_soup=BeautifulSoup(r_sub.content, 'html.parser')
        for a in sub_page_soup.find_all('a', href=True):
            if a["href"] not in second_hrefs and bool(re.search("https://www.mindgate.solutions",a["href"])):
                if a["href"].endswith(".pdf"):
                    pdf_links.append(a["href"])
                else:
                    second_hrefs.append(a["href"])
                    count_sub+=1
                    # print(count_sub)
    ### get unique links 
    all_links=np.unique(first_hrefs+second_hrefs)
    ### Get unique links of pdf 
    pdf_links=list(set(pdf_links))
    return list(all_links),pdf_links

### Clean the text data
def clean_text(text):
    text=fix_text(text)
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)

    # Remove special characters (optional)
    text = re.sub(r'[^A-Za-z0-9\s.,]', '', text)

    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)
    text=text.replace("\n","")
    # Strip leading/trailing whitespace
    text = text.strip()

    # Optional: lowercase
    text = text.lower()
    return text

### Scrape the all main href and sub href except pdf
def scrape_links(links):
    headers = {'Accept-Encoding': 'identity'}
    metadata=[]
    for i in range(len(links)):
        # print(i)
        req = requests.get(links[i], headers=headers)
        final_soup = BeautifulSoup(req.content, 'html.parser', from_encoding="iso-8859-1")
        mydivs_1=final_soup.find_all("div", {"class": "section-container"})
        mydivs_2 = final_soup.find_all("div", {"class": "e-con-inner"})
        page=re.search(r"https:\/\/www\.mindgate\.solutions\/([^\/]+)", links[i])
        page=page.group(1) if page else None 
        # subpage=re.search(r'/([^/?#]+)$', )
        subpage=links[i].rstrip('/').split('/')[-1]
        if subpage==page:
            subpage=None
        uncomment_text=""
        mydivs=mydivs_1+mydivs_2
        for k in range(len(mydivs)-1):
            uncomment_text+=mydivs[k].get_text()
        uncomment_text=clean_text(uncomment_text)
        mdata={"page_content":uncomment_text,"source":links[i],"page": page,"subpage":subpage,"doc_id":str(uuid.uuid4()),"page_number":None}
        metadata.append(mdata)
    return metadata

### Scrape the pdfs
def scrape_pdf(u_pdf_links):
    metadata_pdf = []
    for i in range(len(u_pdf_links)):
        # PDF link
        pdf_url = u_pdf_links[i]
        
        # Extract PDF file name from URL
        name_pdf = pdf_url.rstrip('/').split('/')[-1]
        
        # Download PDF file
        response = requests.get(pdf_url)
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF. Status code: {response.status_code}")
        
        # Load PDF from bytes
        pdf_doc = fitz.open(stream=response.content, filetype="pdf")
        
        
        
        # Process each page
        for page_number, page in enumerate(pdf_doc, start=1):
            page_text = page.get_text()
            page_text=clean_text(page_text)
            mdata = {
                "page": name_pdf,
                "source": pdf_url,
                "page_number": page_number,
                "page_content": page_text.strip(),
                "doc_id":str(uuid.uuid4()),
                "subpage":None
                
            }
        
            metadata_pdf.append(mdata)
    return metadata_pdf

def scrape_all_data():
    all_links,pdf_links=get_all_links()
    metadata_link_scrape=scrape_links(all_links)
    metadata_pdf=scrape_pdf(pdf_links)
    metadata_link_scrape.extend(metadata_pdf)
    return metadata_link_scrape


start=time.time()
data=scrape_all_data()
print(time.time()-start)

with open(r"metdata_newest.json","w") as file:
    json.dump(data,file,indent=4) 