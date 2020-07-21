import pandas as pd
import streamlit as st
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
from vega_datasets import data
from pandasql import sqldf


#initialize local and global variable using pandasql
pysqldf = lambda q: sqldf(q, globals())


events_df = pd.read_csv (r'athlete_events.csv')


gdp_df = pd.read_excel (r'Gapminder GDP data.xlsx', sheet_name='countries_and_territories')

worldcities_df = pd.read_excel(r'olympic_city_country.xlsx', sheet_name='Sheet1')

worldcities_df= worldcities_df.drop_duplicates()


# Cleaning of the data
events_df['Team'] = events_df['Team'].str.replace(r'[-][0-9]', '')
events_df.loc[events_df.NOC=='USA', 'Team'] = "United States"
events_df.loc[events_df.NOC=='GBR', 'Team'] = "United Kingdom"
events_df.loc[events_df.NOC=='DEN', 'Team'] = "Denmark"
events_df.loc[events_df.NOC=='URS', 'Team'] = "Russia"

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

country_name = st.sidebar.selectbox(
'Choose your country name:',
       final_df.sort_values(by=['Country']).Country.unique())
       
#some data manipulations    
final_df_1 = final_df.copy()

final_df = final_df[final_df['Team'].str.contains(country_name)]

final_df['medal_won']= (final_df['Medal']=='Gold') | (final_df['Medal']=='Silver') | (final_df['Medal']=='Bronze')

final_df_1['medal_won']= (final_df_1['Medal']=='Gold') | (final_df_1['Medal']=='Silver') | (final_df_1['Medal']=='Bronze')


st.header('Data')
st.write(final_df.head(100))


####### For Summer Olympics
st.write("Summer Olympics hosted by "+ country_name)
final_df_summer = final_df[final_df['Season']== 'Summer']


line = alt.Chart(final_df_summer).mark_line(point=True).encode(
    x=alt.X('Year:T', axis=alt.Axis(title='Year')),
    y=alt.Y('sum(medal_won):Q', axis=alt.Axis(title='Medals Won')),
    tooltip=['sum(medal_won)']
)

olympic_year = final_df_summer[final_df_summer['Country']== final_df_summer['Country Name']]

#st.write(olympic_year.head(100))


bar = alt.Chart(olympic_year).mark_bar(color='#f8a95c').encode(
    x=alt.X('Year:T', axis=alt.Axis(title='Year')),
    y=alt.X('sum(medal_won):Q', axis=alt.Axis(title='Medals Won')),
)

text = bar.mark_text(
    align='left',
    baseline='middle',
    dx=7
).encode(
    text='year(Year):T'
)

test = st.altair_chart(alt.layer(bar, line, text).configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))


#For Winter Olympics
st.write("Winter Olympics hosted by "+ country_name)
final_df_winter = final_df[final_df['Season']== 'Winter']

line_1 = alt.Chart(final_df_winter).mark_line(point=True).encode(
    x=alt.X('Year:T', axis=alt.Axis(title='Year')),
    y=alt.Y('sum(medal_won):Q', axis=alt.Axis(title='Medals Won')),
    tooltip=['sum(medal_won)']
)

olympic_year_1 = final_df_winter[final_df_winter['Country']== final_df_winter['Country Name']]


bar_1 = alt.Chart(olympic_year_1).mark_bar(color='#f8a95c').encode(
    x=alt.X('Year:T', axis=alt.Axis(title='Year')),
    y=alt.X('sum(medal_won):Q', axis=alt.Axis(title='Medals Won')),
)


text_1 = bar_1.mark_text(
    align='left',
    baseline='middle',
    dx=7
).encode(
    text='year(Year):T'
)

test_1 = st.altair_chart(alt.layer(bar_1, line_1, text_1).configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))

###################### Compute host Percentages

medals_on_all = pysqldf("""SELECT 
                      Year, `Country Name`, sum(medal_won) as Medals_Won
                  FROM final_df_1 where `Country Name` is not NULL and Season= 'Summer'
                  and Team in (select Country from final_df_1)
                  group by Year, `Country Name`
                  having Year > 1990;""")
                  
medals_when_hosted = pysqldf("""SELECT 
                      Year, `Country Name`, sum(medal_won) as Medals_Won
                  FROM final_df_1  where `Country Name` is not NULL
                    and (Year, `Country Name`) in (select Year, Country from final_df_1)
                    and Season= 'Summer'
                  group by Year, `Country Name`
                  having Year > 1992;""")
                  
st.write(medals_on_all)
st.write(medals_when_hosted.head(100))

medals_diff = pysqldf("""select MA.`Country Name`, MA.Year,
              case when MA.Year < MH.Year then 'Before'
                   when MA.Year > MH.Year then 'After'
                   when MA.Year = MH.Year then 'Hosted'
              end as Before_after,
              MH.Medals_won as Medals_When_Hosted,
              MA.Medals_won as Medals_When_Not_Hosting,
              100+ ((MA.Medals_Won- MH.Medals_Won) / cast(MH.Medals_Won as float)) *100 as Medal_Difference
              from medals_on_all MA inner join medals_when_hosted MH on
              MA.`Country Name`= MH.`Country Name`
              and (MA.Year <= MH.Year + 4 and MA.Year >= MH.Year -4);""")
                  
st.write(medals_diff)

domain = ['Before', 'Hosted', 'After']
range_= ['#4b78a8', '#f8a95c', '#4b78a8']

grouped_bar = alt.Chart(medals_diff).mark_bar().encode(
    x='Year:O',
    y=alt.X('sum(Medal_Difference):Q', axis=alt.Axis(title='% of Medals Difference')),
    color= alt.Color('Before_after:N', scale=alt.Scale(domain=domain, range=range_)),
    column='Country Name:N'
)

test_1 = st.altair_chart(grouped_bar)



