import pandas as pd
import streamlit as st
import numpy as np
import altair as alt
import matplotlib.pyplot as plt

events_df = pd.read_csv (r'athlete_events.csv')

gdp_df = pd.read_excel (r'Gapminder GDP data.xlsx', sheet_name='countries_and_territories')

worldcities_df = pd.read_excel(r'olympic_city_country.xlsx', sheet_name='Sheet1')

worldcities_df= worldcities_df.drop_duplicates()

gdp_pivoted_df = pd.melt(gdp_df, 
            id_vars='Country Name', 
            value_vars=list(gdp_df.columns[1:]), # list of days of the week
            var_name='Year', 
            value_name='GDP')
            
merged_df = pd.merge(events_df,
                 gdp_pivoted_df,
                 left_on=['Team', 'Year'], 
                 right_on=['Country Name', 'Year'],
                 how='left')

final_df = pd.merge(merged_df,
                 worldcities_df,
                 left_on='City', 
                 right_on='City',
                 how='left')

#print(final_df.head(100))

st.header('Data')
st.write(final_df.head(100))

st.write(worldcities_df.groupby('Country').count())

times_hosted = worldcities_df.groupby('Country').count()


st.subheader('Which countries have hosted Olympics how many times?')

times_hosted = st.bar_chart(times_hosted)


country_list_medals = final_df[(final_df.Medal.notnull()) &
             (final_df.Team==final_df.Country)]['Country']


st.subheader('Medals by Host Country')

medals_by_country = st.bar_chart(country_list_medals.value_counts())

