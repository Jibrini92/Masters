from text_extract import PDF_to_Para
import pandas as pd
def text_extract(df_in):
    df=df_in.copy()
    for i in range(0,len(df)):
        if df.at[i,"status"] !=1: # only extratct pdfs with status 1
            continue 
        path="reports\\"+df.at[i,"Full report path"] #path to individual report
        company=df.at[i,"Company"] # column Company
        paper_year=df.at[i,"Year"] # column year
        print(company," ",str(paper_year), "=  in progress") # to know where error happens if it stops
        df_out=PDF_to_Para(company,paper_year,path) # call PDF_to_Para to extract paragraphs
        csv_out="..\\CSVs_2/"+company+"_"+str(paper_year)+".csv" # write output of each report into sepratae CSV
        df_out.to_csv(csv_out)
        print(company," ",str(paper_year), "=  Done")

df_reports = pd.read_csv('..\\reports\\reports_links.csv')
text_extract(df_reports)