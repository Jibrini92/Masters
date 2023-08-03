import pandas as pd
import fitz


def pdf_scraper(filePath):
    results = [] # list of tuples that store the information as (text, font size, font name) 
    block_num=0
    page_num=0
    pdf = fitz.open(filePath) # filePath is a string that contains the path to the pdf
    for page in pdf:
        dict = page.get_text("dict")
        blocks = dict["blocks"]
        page_num+=1
        for block in blocks:
            block_num+=1
            if "lines" in block.keys():
                spans = block['lines']
                for span in spans:
                    data = span['spans']
                    for lines in data:
                        results.append((lines['text'], lines['size'], lines['font'],block_num,page_num,block["bbox"]))
                            # lines['text'] -> string, lines['size'] -> font size, lines['font'] -> font name, block_num -> order number of the block, 
                            # block["bbox"] -> block box coordinates
    return results

def lines_to_paragaphs(df_in):
    # Groups lines back into paragraphs
    df=df_in.copy()
    df.text.replace({r'[^\x00-\x7F]+':''}, regex=True, inplace=True) # remove non ASCII characters
    # Join up lines belonging to the same paragraph with a new line inbetween
    df['text'] = df[["text","font_size","block_number","page_number"]].groupby(['block_number'])['text'].transform(lambda x: '\n '.join(x))
    # Keep only one instance of each paragraph
    df=df.drop_duplicates(subset='text', keep="first").reset_index(drop=True)
    return df

def bulet_points(df_in):
    # Groups bulletpoints into one paragraphs, not used in current version
    df=df_in.copy()
    for i in range(1,len(df)):
        if all(c in '• –' for c in df.at[i,'text'] ) and df.at[i,'block_number'] > df.at[i-1,'block_number']:
            for j in range(i,len(df)):
                df.at[j,'block_number']=df.at[j,'block_number']-1
    return df

def label_broken_para(df_in):
    #Identifies paragrapsh that could be broken at page end
    df=df_in.copy()
    df["first_part"]=0
    df["second_part"]=0
    for j in range(0,len(df)):
        # Paragraphs not ending with a punctuation mark get the first_part label
        if df.text.at[j][-1] not in [".","!","?"]:
            df.at[j,"first_part"]=1
        # Paragraphs not starting with upper case get the second_part label
        if df.text.at[j][0].isupper() == False:
            df.at[j,"second_part"]=1
    return(df)

def find_other_half(i,df_in):
    # For a paragraph that is labeled first_part, find closes paragraph that is labeled with second half
    # Looks only at the same page or next
    # returns j, the index of the second part given i the index of the first
    j=i
    df=df_in.copy()
    if j > len(df)-2:
        return 0
    while df.at[j,"second_part"] == 0:
        j+=1
        if j > len(df)-2:
            return 0
    if df.at[j,"page_number"] > df.at[i,"page_number"]+1 or df.at[j,"page_number"] == df.page_number.max():
        return 0
    else:
        return j
    
def combine(df_in):
    #combines the disjointed parts of one paragraph
    df=df_in.copy()
    df=label_broken_para(df) # label broken parts
    i=0
    while df.at[i,"page_number"]< df.page_number.max():
        if df.at[i,"first_part"]==1: #identify first_part
            j=find_other_half(i,df) # find the second_part
            if j==0:
                pass
            elif df.at[j,"first_part"]==1:# check for a rare case when paragraph is broken into more than 2 parts
                k=find_other_half(j,df) # find the third part
                if k==0:
                    pass
                else:
                    df.text.at[j]+= " \n "+df.text.at[k]
                    df=df.drop(k).reset_index(drop=True)
                    df.text.at[i]+= " \n "+df.text.at[j]
                    df=df.drop(j).reset_index(drop=True)
            else:
                df.text.at[i]+= " \n "+df.text.at[j]
                df=df.drop(j).reset_index(drop=True)
        i+=1
        if i>=len(df):
            break
    return df
def fonts_to_keep(df_in):
    # identify rarely uused font sizes and discard them
    df=df_in.copy()
    df['font_size_rounded']=round(df['font_size']*2)/2
    font_frequency=dict(df['font_size_rounded'].value_counts()/len(df))
    fonts_to_keep=[k for k, v in font_frequency.items() if v > 0.05]
    df=df[df['font_size_rounded'].isin(fonts_to_keep)].reset_index(drop=True)
    return df

def table_remove(df_in):
    df=df_in.copy()
    df['newpage_count'] = df.apply(lambda x: x["text"].count("\n"), axis=1) #count new lines in paragraph
    #The frequency of new pages - occurances of \n divided by len of the string
    df['newpage_frequency'] = df.apply(lambda x: x["newpage_count"]/ len(x['text']), axis=1) # calculate frequency of new lines
    df=df[df['newpage_frequency'] < 0.1] #discard paragrapsh with high frequency of new lines
    df=df.drop(columns=['newpage_count', 'newpage_frequency'])
    return df

def PDF_to_Para(company_name,paper_year,path):
    results=pdf_scraper(path) # read pdf data
    results_df=pd.DataFrame(results, columns=["text","font_size","font","block_number","page_number","coordinates"])# transform into DataFrame
    results_df['X_center'] = results_df.apply(lambda row: (row.coordinates[2] + row.coordinates[0])/2, axis = 1)
    results_df['Y_center'] = results_df.apply(lambda row: (row.coordinates[3] + row.coordinates[1])/2, axis = 1)
    results_df=fonts_to_keep(results_df) #Discard rarley used font size (titles and footnotes)
    results_df=lines_to_paragaphs(results_df) # combine lines back into paragraphs
    results_df["text"]=results_df["text"].str.strip() # strip space at the ends of a paragraph
    results_df=results_df[results_df['text'].map(len) > 100].reset_index(drop=True) # discard short paragraphs
    results_df=results_df[results_df["text"].str.contains('.'or'!'or'/?',regex=False)].reset_index(drop=True) # Discard paragraphs with no punctuation 
    results_df=combine(results_df) # combine paragraphs broken by new page
    results_df=table_remove(results_df) # remove tables
    results_df["Company"]=company_name #add company name column
    results_df["year"]=paper_year #add year of the pdf column
    return results_df


