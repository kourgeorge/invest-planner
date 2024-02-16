import streamlit as st


def header():
    st.image('resources/banner.png', use_column_width=True)


def footer():
    st.write("© All rights reserved to George Kour. 2024 (v0.3)")
    st.write("Disclaimer: The use of this application is at your own risk. "
             "The information and results provided on this application are for informational purposes only and do not constitute financial advice or consultation. "
             "Users are advised to independently verify any data and consult with qualified professionals for personalized financial guidance. "
             "We do not assume any responsibility for the accuracy, completeness, or suitability of the information provided. "
             "By using this application, you acknowledge and accept that your financial decisions are solely your responsibility.")
