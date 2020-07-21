import pandas as pd
import streamlit as st
import numpy as np
import altair as alt
import matplotlib.pyplot as plt
from vega_datasets import data


events_df = pd.read_csv (r'athlete_events.csv')

population_df = pd.read_csv (r'population_total.csv')

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
            value_name='GDP_pc')
            
gdp_merged_df = pd.merge(events_df,
                 gdp_pivoted_df,
                 left_on=['Team', 'Year'], 
                 right_on=['Country Name', 'Year'],
                 how='left')
                 

pop_pivoted_df = pd.melt(population_df, 
            id_vars='country', 
            value_vars=list(population_df.columns[1:]), # list of days of the week
            var_name='Year', 
            value_name='Population')

pop_pivoted_df['Year'] = pop_pivoted_df['Year'].astype(int)

pop_merged_df = pd.merge(gdp_merged_df,
                 pop_pivoted_df,
                 left_on=['Country Name', 'Year'], 
                 right_on=['country', 'Year'],
                 how='left')

#dataframe for population and gdp only
pop_gdp_df = pd.merge(gdp_pivoted_df,
                 pop_pivoted_df,
                 left_on=['Country Name', 'Year'], 
                 right_on=['country', 'Year'],
                 how='left')  

final_df = pd.merge(pop_merged_df,
                 worldcities_df,
                 left_on='City', 
                 right_on='City',
                 how='left')


#print(final_df.head(100))

#print(final_df.head(100))
viz_year = st.sidebar.selectbox(
'Choose a year to compare Medals won vs GDP',
       final_df.sort_values(by=['Year']).Year.unique())
       
       
country_name = st.sidebar.selectbox(
'Choose your country name:',
       final_df.sort_values(by=['Country Name']).country.unique())

       
#some data manipulations from the filter
final_df['medal_won']= (final_df['Medal']=='Gold') | (final_df['Medal']=='Silver') | (final_df['Medal']=='Bronze')

final_df['GDP']= final_df['GDP_pc'] * final_df['Population']

final_df['GDP']= final_df[['GDP']]/10**9


pop_gdp_df['GDP']= pop_gdp_df['GDP_pc'] * pop_gdp_df['Population']/10**9


#export unfiltered dataset
#final_df.to_csv(r'Merged_dataset.csv')

final_df_year = final_df[final_df['Year']== viz_year]
final_df_year = final_df_year[final_df_year['Population'] >= 10**6]



st.header('Data')
st.write(final_df_year.head(100))

st.write("Medals Won vs GDP Per Capita in the year " + str(viz_year))
st.text("Correlation Coefficient:")
st.write(round(final_df_year['GDP_pc'].corr(final_df_year['medal_won']), 2))

medal_won_vs_gdp_pc = alt.Chart(final_df_year).mark_circle(size=60).encode(
    x= alt.X('GDP_pc:Q', axis=alt.Axis(title='GDP per Capita')),
    y= alt.Y('sum(medal_won):Q', axis=alt.Axis(title='Sum of Medals Won')),
    tooltip=['Country Name', 'GDP', 'Population', 'sum(medal_won)']
)

chart_1 = st.altair_chart(alt.layer(medal_won_vs_gdp_pc).configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))

st.write("Medals Won vs Total GDP in the year " + str(viz_year))
st.text("Correlation Coefficient: ")
st.write(round(final_df_year['GDP'].corr(final_df_year['medal_won']), 2))

medal_won_vs_gdp = alt.Chart(final_df_year).mark_circle(size=60).encode(
    x= alt.X('GDP:Q', axis=alt.Axis(title='Total GDP (in millions)')),
    y= alt.Y('sum(medal_won):Q', axis=alt.Axis(title='Sum of Medals Won')),
    tooltip=['Country Name', 'GDP', 'Population', 'sum(medal_won)']
).interactive()

chart_2 = st.altair_chart(alt.layer(medal_won_vs_gdp).configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))


corr_year_list= []
for year in final_df.sort_values(by=['Year']).Year.unique():
  year_data = final_df[final_df.Year==year]
  year_data= year_data[year_data['Season'] == 'Summer']
  if not year_data.empty:
    corr_year_list.append([year, year_data['GDP'].corr(year_data['medal_won']),
        year_data['Population'].corr(year_data['medal_won']),
        year_data['GDP_pc'].corr(year_data['medal_won'])])

corr_year_list = pd.DataFrame(corr_year_list)

corr_year_list.columns= ['Year', 'Corr_GDP', 'Corr_Popn', 'Corr_GDP_pc']

corr_year_list['Year'] = pd.to_datetime(corr_year_list['Year'], format='%Y')


# Display the created table- Correlation of all 3 on Year
st.write(corr_year_list)

# Save Dataframe if needed
#corr_year_list.to_csv(r'Correlation_Table.csv')


# Begin Plotting

year_gdp_corr = alt.Chart(corr_year_list).mark_line(color="#f8a95c", point=True).encode(
    x='Year:T',
    y=alt.Y('Corr_GDP:Q', axis=alt.Axis(title='Correlation Value')),
    tooltip=['Corr_GDP:Q']
)

year_gdp_pc_corr = alt.Chart(corr_year_list).mark_line(color="#4b78a8", point=True).encode(
    x='Year:T',
    y=alt.Y('Corr_GDP_pc:Q', axis=alt.Axis(title='Correlation Value')),
    tooltip=['Corr_GDP_pc:Q']
)

year_gdp_pop_corr = alt.Chart(corr_year_list).mark_line(color="#57A44C", point=True).encode(
    x='Year:T',
    y=alt.Y('Corr_Popn:Q', axis=alt.Axis(title='Correlation Value')),
    tooltip=['Corr_Popn:Q']
)

chart_01 = st.altair_chart(alt.layer(year_gdp_corr, year_gdp_pc_corr, year_gdp_pop_corr).configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))

####### End of 3x line graph ######

####### Start of Country's medals vs GDP plot #############

print(country_name)

final_df_copy= final_df[final_df['Team'] == country_name].copy()

### GDP plot
base = alt.Chart(final_df_copy).encode(
    alt.X('Year:T', axis=alt.Axis(title=None))
)

line_1 = base.mark_line(stroke='#5276A7').encode(
    alt.Y('sum(medal_won):Q',
          axis=alt.Axis(title='Medals Won')),
          tooltip=['Country Name', 'GDP', 'Population', 'sum(medal_won)', 'Year'],
)

line_2 = base.mark_line(opacity=0.8, color='#f8a95c').encode(
    alt.Y('GDP:Q',
          axis=alt.Axis(title='Gross Domestic Product (GDP)', titleColor='#f8a95c'))
)

test_3 = st.altair_chart(alt.layer(line_1, line_2).resolve_scale(y = 'independent').configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))


### Population Plot
base_1 = alt.Chart(final_df_copy).encode(
    alt.X('Year:T', axis=alt.Axis(title=None))
)

line_3 = base.mark_line(stroke='#5276A7').encode(
    alt.Y('count(medal_won):Q',
          axis=alt.Axis(title='Medals Won')),
          tooltip=['Country Name', 'GDP', 'Population', 'count(medal_won)', 'Year'],
)

line_4 = base.mark_line(opacity=0.8, color='#57A44C').encode(
    alt.Y('Population:Q',
          axis=alt.Axis(title='Population', titleColor='#57A44C'))
)

test_4 = st.altair_chart(alt.layer(line_3, line_4).resolve_scale(y = 'independent').configure_axis(
    grid=False
).properties(
    width=600,
    height=400
))


## Bottom 5 GDP to Medals Plot
#st.write(pop_gdp_df[pop_gdp_df.Year== 2016].sort_values(by='GDP').head(5))

bot_gdp = pop_gdp_df[pop_gdp_df.Year== 2016].sort_values(by='GDP').head(5)

st.subheader("Bottom GDP Countries")
st.write(bot_gdp)


for country in bot_gdp.country:
  final_df_copy= final_df[final_df['Team'] == country].copy()

  st.write("Country: " + country)
  base = alt.Chart(final_df_copy).encode(
      alt.X('Year:T', axis=alt.Axis(title=None))
  )
  
  line_1 = base.mark_line(stroke='#5276A7').encode(
      alt.Y('sum(medal_won):Q',
            axis=alt.Axis(title='Medals Won', titleColor='#5276A7')),
            tooltip=['Country Name', 'GDP', 'Population', 'sum(medal_won)', 'Year'],
  )
  
  line_2 = base.mark_line(opacity=0.8, color='#f8a95c').encode(
      alt.Y('GDP:Q',
            axis=alt.Axis(title='Gross Domestic Product (GDP) in Billions', titleColor='#f8a95c'))
  )
  
  test_3 = st.altair_chart(alt.layer(line_1, line_2).resolve_scale(y = 'independent').configure_axis(
      grid=False
  ).properties(
      width=600,
      height=400
  ))


## Top 5 GDP to Medals Plot
#st.write(pop_gdp_df[pop_gdp_df.Year== 2016].sort_values(by='GDP').head(5))

top_gdp = pop_gdp_df[pop_gdp_df.Year== 2016].sort_values(by='GDP', ascending=False).head(5)

st.subheader("Top GDP Countries")
st.write(top_gdp)

for country in top_gdp.country:
  final_df_copy= final_df[final_df['Team'] == country].copy()

  st.write("Country: " + country)
  base = alt.Chart(final_df_copy).encode(
      alt.X('Year:T', axis=alt.Axis(title=None))
  )
  
  line_1 = base.mark_line(stroke='#5276A7').encode(
      alt.Y('sum(medal_won):Q',
            axis=alt.Axis(title='Medals Won', titleColor='#5276A7')),
            tooltip=['Country Name', 'GDP', 'Population', 'sum(medal_won)', 'Year'],
  )
  
  line_2 = base.mark_line(opacity=0.8, color='#f8a95c').encode(
      alt.Y('GDP:Q',
            axis=alt.Axis(title='Gross Domestic Product (GDP) in Billions', titleColor='#f8a95c'))
  )
  
  test_3 = st.altair_chart(alt.layer(line_1, line_2).resolve_scale(y = 'independent').configure_axis(
      grid=False
  ).properties(
      width=600,
      height=400
  ))
