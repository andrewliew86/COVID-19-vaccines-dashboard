# -*- coding: utf-8 -*-
"""
Script for constructing a dashboard that shows the latest publications and vaccination rates for COVID-19
"""
import requests
import numpy as np
import pandas as pd
from Bio import Entrez
from Bio import Medline
import streamlit as st
import plotly.graph_objects as go

# Create visualization of the number of new vaccinations (per million) over time in Thailand, Australia, Malaysia and New Zealand 

# Call OWID API and get a json response object for the vaccination graphs
resp = requests.get('https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/owid-covid-data.json')
json_data = resp.json()

# Call OWID API and get vaccines that have been approved in different countries and create a dictionary with countries as keys and approved vaccines as values
loc_data = pd.read_csv('https://raw.githubusercontent.com/owid/covid-19-data/master/public/data/vaccinations/locations.csv')
vaccines_country_dict = pd.Series(loc_data.vaccines.values,index=loc_data.iso_code).to_dict()
#%%
# Create seperate dataframes for the different countries for plotting vaccinations
# Look at data from THA, AUS, MYS, NZL
country_dict = {'THA': 'Thailand', 
               'AUS': 'Australia', 
               'MYS': 'Malaysia', 
               'NZL': 'New Zealand'}

# Create empty list to append dataframe
df_list = []

# Loop through dictionary of countries to extract vaccine data for each country
for k, v in country_dict.items():
    dates_list = []
    vaccines_per_mil_list = []
    country_list = []
    
    # Get vaccine data for specific country
    for vac in json_data[k]['data']:
        dates_list.append(vac.get('date'))
        vaccines_per_mil_list.append(vac.get('new_vaccinations_smoothed_per_million', np.nan))
        country_list.append(v)
    # Get vaccine data into a dataframe and append dataframe into a list
    df = pd.DataFrame({'Dates':dates_list,
                   'Vaccines': vaccines_per_mil_list,
                   'Country': country_list})
    df_list.append(df)
        
# Concatenate the list of dataframes for all 4 countries into a single dataframe and set the 'Dates' column as datetime and index
concat_df = pd.concat(df_list)
concat_df['Dates'] = pd.to_datetime(concat_df['Dates'], format='%Y-%m-%d')
concat_df.dropna(inplace=True) # Remove nans
# Vaccinations really only started this year so only show data 

# Create seperate dataframes for each country
thai_df = concat_df.loc[concat_df['Country'] == 'Thailand']
malaysia_df = concat_df.loc[concat_df['Country'] == 'Malaysia']
aus_df = concat_df.loc[concat_df['Country'] == 'Australia']
nz_df = concat_df.loc[concat_df['Country'] == 'New Zealand']
#%%
# Extract titles and URLs for the PubMed articles on COVID-19 vaccine research
Entrez.email = 'example_email@yahoo.com.au'

# Use cache decorator here to improve streamlit performance by saving the results each time you run this function 
@st.cache
def retrive_pubs(term, max_count = 10):
    """
    Retrive top n latest publication titles and PMIDs from PubMed (keyword search)

    Parameters
    ----------
    term : string
        Keyword search string. The default is 'COVID-19 vaccines'.
    max_count : integer, optional
        Number of results to return. The default is 10.

    Returns
    -------
    Dictionary of publication titles as keys and paper urls for the keyword search from PubMed

    """
    h = Entrez.esearch(db='pubmed', retmax=max_count, term=term)
    result = Entrez.read(h)
    print("Number of publications on PubMed containing the term '{0}': {1}".format(term, result['Count']))
    ids = result['IdList']
    # fetch the publication titles from PubMed using fetch
    h = Entrez.efetch(db='pubmed', id=ids, rettype='medline', retmode='text')
    records = Medline.parse(h)
    # Store titles and create individual urls links for each paper title (so that they are clickable at a later stage) based on PMIDs
    titles = [record.get('TI', '?') for record in records]
    urls = [f"https://pubmed.ncbi.nlm.nih.gov/{url}/".format(url) for url in ids]
    dict_title_url = dict(zip(titles,urls))
    return dict_title_url
    
paper_dict = retrive_pubs('COVID-19 vaccines')    
    
#%%
# Build Streamlit app: left panel (10 latest paper titles on vaccines) and right panel (number of vaccinations) 
# Create title of dashboard
st.title("COVID-19 vaccinations dashboard")
st.markdown(
"""
This dashboard shows the number of vaccinations that have been delivered in Australia, Thailand, Malaysia or New Zealand. Information on the vaccines approved in each country
as well as the latest scientific publcations on COVID-19 vaccines (from PubMed) are also shown.        

Instructions: select your country of choice from the drop-down list and wait for a few seconds for the chart to be updated.
x-axis shows the dates while y-axis shows the number of vaccines administered (per million).
"""
)

st.markdown("#### " +"Select country to display data")

selected_metrics = st.selectbox(label=" ", options=['Thailand','Australia','Malaysia', 'New Zealand']
)


# Create lineplot with vaccine approval info
fig = go.Figure()
if selected_metrics == 'Thailand':
    st.markdown(f"Vaccines approved in Thailand: {vaccines_country_dict['THA']}".format(vaccines_country_dict['THA']))
    fig.add_trace(go.Scatter(x=thai_df.Dates, y=thai_df.Vaccines, mode='lines', name='Thailand', hoverinfo = 'y', line = dict(width = 3, color ='red')))
if selected_metrics == 'Australia':
    st.markdown(f"Vaccines approved in Australia: {vaccines_country_dict['AUS']}".format(vaccines_country_dict['AUS']))
    fig.add_trace(go.Scatter(x=aus_df.Dates, y=aus_df.Vaccines, mode='lines', name='Australia', hoverinfo = 'y', line = dict(width = 3, color ='green')))
if selected_metrics == 'Malaysia':
    st.markdown(f"Vaccines approved in Malaysia: {vaccines_country_dict['MYS']}".format(vaccines_country_dict['MYS']))
    fig.add_trace(go.Scatter(x=malaysia_df.Dates, y=malaysia_df.Vaccines, mode='lines', name='Malaysia', hoverinfo = 'y', line = dict(width = 3, color ='blue')))
if selected_metrics == 'New Zealand':
    st.markdown(f"Vaccines approved in New Zealand: {vaccines_country_dict['NZL']}".format(vaccines_country_dict['NZL']))
    fig.add_trace(go.Scatter(x=nz_df.Dates, y=nz_df.Vaccines, mode='lines', name='New Zealand', hoverinfo = 'y', line = dict(width = 3, color ='yellow')))

# Remove gridlines and then show figure
fig.update_layout(yaxis_title="Number of vaccines administered (per million)")
fig.update_xaxes(showgrid=False)
fig.update_yaxes(showgrid=False)
st.plotly_chart(fig, use_container_width=True)


# Show a list of COVID-19 vaccine realated publication titles that users can click and visit on PubMed
st.title("The 10 latest publications related to COVID-19 vaccines from PubMed.gov")
st.markdown("***")  # Create some space
st.markdown("#### " +"Note: This list of publications is updated everytime this dashboard is refreshed")
st.markdown("***")  # Create some space
# Use a for loop to loop through the list of paper titles and urls and create seperate markdowns
for n, (k, v) in enumerate(paper_dict.items(), start=1):
    link = f"{n}. {k} [Link to PubMed]({v})".format(n, k, v)
    st.markdown(link, unsafe_allow_html=True)




    
# To run the streamlit app, go to command prompt and navigate to the folder containing this .py file using 'cd'
# 'Activate' the anaconda virutal environment containing the streamlit library... type in activate streamlit_app
# Type 'streamlit run dashboard_data.py' 
# Obviously change the name of the .py file accordingly
