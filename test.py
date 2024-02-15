from vega_datasets import data
import altair as alt

if __name__ == '__main__':
    source = data.barley()

    alt.Chart(source).mark_bar().encode(
        x='year:O',
        y='sum(yield):Q',
        color='year:N',
        column='site:N')

    import altair as alt
    import pandas as pd

    data = pd.DataFrame({'x': ['A', 'B', 'C', 'D', 'E'],
                         'y': [5, 3, 6, 7, 2]})
    alt.Chart(data).mark_bar().encode(
        x='x',
        y='y',
    )


    x=1



