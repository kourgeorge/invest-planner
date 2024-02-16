import streamlit as st
from common_components import footer, header

st.set_page_config(page_title='Planit', page_icon="📈")
header()

st.markdown(
    """# Welcome to Planit 📈: Your Mortgage Companion

Planit is your go-to tool for making informed financial decisions, especially when it comes to mortgages. Our user-friendly interface and intuitive design make it easy to compare different mortgage options and recycle existing ones.

### 1. Mortgage Comparison

Make better financial decisions by comparing various mortgage options effortlessly. 
Planit provides a range of tools and clear visuals to help you understand the impact of different terms, interest rates, and loan amounts.

### 2. Recycling Mortgages

Already have a mortgage? No problem! Planit allows you to recycle existing mortgages, helping you visualize the potential benefits of refinancing or adjusting terms.

## Getting Started

Ready to take control of your mortgage journey? Follow these simple steps:

1. **Compare Mortgages:**
    - Navigate to the "compare app" tab.
    - Enter details like loan amount, interest rate, and term. or upload from a file.
    - Explore the visually appealing graphics to understand the impact of different scenarios.

2. **Recycle Your Mortgage:**
    - Visit the "recycle app" tab.
    - Input details of your existing mortgage.
    - Visualize the potential benefits of refinancing or adjusting terms.

3. **Save and Share:**
    - Save your mortgage scenarios for future reference.
    - Print a visually appealing and understandable report.
    - Share your findings with trusted advisors or family members.

## Why Planit?

- **Simple and Pretty Graphics:** We believe financial tools should be easy to use and visually appealing. Our graphics simplify complex information for better understanding.

- **Accessible Tools:** Planit provides accessible tools for users of all experience levels. No financial jargon — just straightforward information.

- **Intuitive Design:** Navigate through the application effortlessly. Planit's intuitive design ensures a seamless user experience.

Make Planit your financial companion and take the guesswork out of your mortgage decisions!

"""
)

st.divider()
footer()
