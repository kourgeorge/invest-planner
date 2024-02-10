from flask import Flask, render_template, request
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

from loan import Loan
from mortgage import Mortgage

app = Flask(__name__)


# Assuming Loan and Mortgage classes are already defined

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/calculate', methods=['POST'])
def calculate():
    loans = []

    # Collect loan information from the form
    num_of_loans = int(request.form.get('num_of_loans', 1))

    for i in range(num_of_loans):
        loan_amount = float(request.form[f'loan_amount_{i}'])
        interest_rate = float(request.form[f'interest_rate_{i}'])
        num_of_months = int(request.form[f'num_of_months_{i}'])
        grace_period = int(request.form[f'grace_period_{i}'])

        # Create Loan objects and add to the list
        loan = Loan(loan_amount, interest_rate, num_of_months, grace_period)
        loans.append(loan)

    # Create Mortgage object
    mortgage = Mortgage(loans)

    # Calculate results
    total_interest = mortgage.total_interest_payments()
    total_principal = mortgage.total_payments()
    amortization_schedule_combined = mortgage.amortization_schedule

    # Generate and save graphs
    plot1, plot2 = generate_plots(amortization_schedule_combined)

    # Encode plots to be displayed in HTML
    encoded_plot1 = encode_image(plot1)
    encoded_plot2 = encode_image(plot2)

    # Render the template with the encoded plots and results
    return render_template('result.html', plot1=encoded_plot1, plot2=encoded_plot2,
                           total_interest=total_interest, total_principal=total_principal)


def generate_plots(amortization_schedule):
    # Your plotting logic here
    # ...

    # For illustration, let's create dummy plots
    plt.figure(figsize=(8, 4))
    plt.plot(amortization_schedule['Month'], amortization_schedule['Remaining Balance'], label='Remaining Balance')
    plt.title('Remaining Balance Over Time')
    plt.xlabel('Month')
    plt.ylabel('Remaining Balance')
    plot1 = plt.gcf()

    plt.figure(figsize=(8, 4))
    plt.plot(amortization_schedule['Month'], amortization_schedule['Monthly Payment'], label='Monthly Payment')
    plt.title('Monthly Payment Over Time')
    plt.xlabel('Month')
    plt.ylabel('Monthly Payment')
    plot2 = plt.gcf()

    return plot1, plot2


def encode_image(plot):
    # Save the plot to a BytesIO object and encode as base64
    image_stream = BytesIO()
    plot.savefig(image_stream, format='png')
    image_stream.seek(0)
    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')
    plt.close()  # Close the plot to free up resources
    return encoded_image


if __name__ == '__main__':
    app.run(debug=True)
