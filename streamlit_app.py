import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objs as go
import numpy as np
import time 

# Set page configuration
st.set_page_config(page_title="ANALYTICA LabsX", layout="wide", page_icon="📈")

# Fetching stock data from Yahoo Finance
def get_stock_data(symbol, time_range="10y"):
    stock = yf.Ticker(symbol)
    stock_data = stock.history(period=time_range)

    if stock_data.empty:
        st.error("Error: Unable to fetch stock data.")
        return None

    stock_data = stock_data[['Open', 'High', 'Low', 'Close', 'Volume']]
    return stock_data

# Calculate price differences based on days
def calculate_price_differences(stock_data):
    if len(stock_data) < 30:
        st.error("Insufficient historical data for price difference calculations.")
        return None, None, None, None, None
    
    daily_diff = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-2]
    weekly_diff = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-6]
    monthly_diff = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-22]
    days_90_diff = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-90]
    months_6_diff = stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[-132]
    return daily_diff, weekly_diff, monthly_diff, days_90_diff, months_6_diff

# Calculate a regression curve for the data and bands
def calculate_regression_curve(x_values, y_values, degree=2, num_bands=4):
    x_numeric = np.arange(len(y_values))  # Use an array of indices as numeric values
    y_numeric = y_values.values  # Extract the actual array from the pandas Series

    # Limit polynomial degree to max of (data length - 1)
    # Ensures that we do not request a degree higher than available data points
    if degree > len(y_numeric) - 1:
        degree = len(y_numeric) - 1

    x_transformed = x_numeric / np.max(x_numeric)  # Normalize x values to [0, 1]
    
    # Apply polynomial fit
    coefficients = np.polyfit(x_transformed, y_numeric, degree)
    polynomial = np.poly1d(coefficients)
    
    # Calculate regression values based on fitted polynomial
    regression_values = polynomial(x_transformed)

    # Calculate residuals for determining standard deviation bands
    residuals = y_numeric - regression_values
    std_residuals = np.std(residuals)
    
    bands = []
    colors = ['green', 'blue', 'red', 'purple']  # Define unique colors for the bands
    band_annotations = [
        ('Take Profit Level 1', 'black', 'DCA Buy Level 1', 'green'),
        ('Take Profit Level 2', 'blue', 'DCA Buy Level 2', 'blue'),
        ('Take Profit Level 3', 'red', 'DCA Buy Level 3', 'red'),
        ('Take Profit Level 4', 'purple', 'DCA Buy Level 4', 'purple')
    ]

    for i in range(1, num_bands + 1):
        lower_band = regression_values - i * 1.5 * std_residuals
        upper_band = regression_values + i * 1.5 * std_residuals
        bands.append((lower_band, upper_band, colors[i - 1], band_annotations[i - 1]))

    return regression_values, bands, degree

# Main app function
def app():
    # Add Google Analytics tracking
    st.markdown('''
        <!-- Google tag (gtag.js) -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-EQ0NXTHK2E"></script>
        <script>
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());

          gtag('config', 'G-EQ0NXTHK2E');
        </script>
    ''', unsafe_allow_html=True)

    st.markdown("<h1 style='text-align: center; font-size: 64px;'>📉 DCA NAVIGATOR 📈</h1>", unsafe_allow_html=True)
    # Adding your company name to the sidebar
    st.sidebar.markdown("<h2 style='text-align: center; font-size: 40px;'>ANALYTICA Labs</h2>", unsafe_allow_html=True)
  
    # Add the statement with a link to Yahoo Finance
    st.sidebar.markdown(
        "<h5 style='text-align: center;'>Powered by <a href='https://finance.yahoo.com' style='color: blue;'>Yahoo Finance</a></h5>",
        unsafe_allow_html=True
    )

    # Text input for stock ticker
    symbol = st.sidebar.text_input(
        "Enter a stock ticker (e.g., AAPL, TSLA):",
        "AAPL", 
        help="Enter the stock symbol you wish to look up. All valid tickers can be found on Yahoo Finance. Examples include 'AAPL' for Apple Inc. and 'TSLA' for Tesla Inc."
    ).upper()

    chart_types = ["Candlestick Chart", "Line Chart"]
    chart_type = st.sidebar.radio("Select Chart Type:", chart_types, help="To identify price action events for DCA entry use the Line Chart")

    # Polynomial regression settings
    degree = st.sidebar.slider(
        "Select Polynomial Degree for Regression Curve", 
        min_value=1, 
        max_value=100, 
        value=2, 
        step=1,
        format="%d", 
        help="## Effect of Polynomial Degree on Stock Price Chart\n\n"
             "* **High Polynomial Degree:**\n"
             "  - You will see price action events more frequently, resulting in more DCA buying opportunities with smaller price changes. This allows you to invest smaller amounts more often, potentially diversifying your investments but may also lead to higher transaction fees.\n"
             "\n"
             "* **Low Polynomial Degree:**\n"
             "  - You will encounter price action events less often, resulting in fewer DCA opportunities with larger price changes. This means you'll invest larger amounts less frequently, which can simplify your investment strategy but might cause you to miss out on some opportunities.\n"
             "\n"
             "## Summary:\n"
             "It's important to decide how often you want to DCA buy, how much to consistently invest each time a DCA price action event occurs, and how this choice affects your overall investment strategy. Each stock/cryptocurrency is subjective to working best with its own specific value. THERE IS NO ONE SET VALUE THAT IS THE HOLY GRAIL. It all depends on your budget and desired frequency of investing."
    )

    # Tooltip with adjusted styling for the tooltip
    st.sidebar.markdown('''
        <style>
            .tooltip {
                position: relative;
                display: inline-block;
                cursor: help;
            }
            .tooltip .tooltiptext {
                visibility: hidden; 
                width: 250px; /* Set the desired width for the tooltip */
                max-height: 300px; /* Set the maximum height for the tooltip */
                background-color: #EFF2F6; 
                color: black; 
                text-align: center; 
                border-radius: 6px; 
                padding: 5px; 
                position: absolute; 
                z-index: 1;
                left: 65%;
                bottom: 100%; /* Adjust the distance below the info icon */
                transform: translateX(-50%);
                overflow-y: auto; /* Add vertical scrollbar when content exceeds max-height */
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Add box shadow with 8px blur and 0.1 opacity */
            }
            .tooltip:hover .tooltiptext {
                visibility: visible;
            }
        </style>
        <div class="tooltip">
            <b style="font-size: 20px;"> 
                NASDAQ TOP STOCKS LIST
            </b>
            <span class="tooltiptext">
                "Apple Inc. (AAPL)",
                "Microsoft Corporation (MSFT)",
                "Alphabet Inc. (GOOG, GOOGL)",
                "Amazon.com Inc. (AMZN)",
                "Tesla Inc. (TSLA)",
                "Meta Platforms Inc. (META)",
                "NVIDIA Corporation (NVDA)",
                "PepsiCo Inc. (PEP)"
            </span>
        </div>
    ''', unsafe_allow_html=True)

    if symbol:
        stock_data = get_stock_data(symbol)

        if stock_data is not None:
            if len(stock_data) < 30:
                st.error("Insufficient historical data for price difference calculations.")
                return
            
            stock_info = yf.Ticker(symbol).info
            stock_name = stock_info.get('longName', stock_info.get('shortName', symbol))

            # Display stock name with customized font size and weight
            st.markdown(f"<p style='font-size:40px; text-align: center; font-weight:bold;'>{stock_name}</p>", unsafe_allow_html=True)

            daily_diff, weekly_diff, monthly_diff, days_90_diff, months_6_diff = calculate_price_differences(stock_data)

            # Handle potential None returns from calculating differences
            if daily_diff is None: 
                return

            percentage_difference_daily = (daily_diff / stock_data['Close'].iloc[-2]) * 100
            percentage_difference_weekly = (weekly_diff / stock_data['Close'].iloc[-6]) * 100
            percentage_difference_monthly = (monthly_diff / stock_data['Close'].iloc[-22]) * 100
            percentage_difference_days_90 = (days_90_diff / stock_data['Close'].iloc[-90]) * 100
            percentage_difference_months_6 = (months_6_diff / stock_data['Close'].iloc[-132]) * 100

            latest_close_price = stock_data['Close'].iloc[-1]
            max_52_week_high = stock_data['Close'].rolling(window=252).max().iloc[-1]
            min_52_week_low = stock_data['Close'].rolling(window=252).min().iloc[-1]

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Close Price", f"${latest_close_price:,.4f}")
            with col2:
                st.metric("Daily Price Difference", f"${daily_diff:,.4f}", f"{percentage_difference_daily:+.2f}%")
            with col3:
                st.metric("Weekly Price Difference", f"${weekly_diff:,.4f}", f"{percentage_difference_weekly:+.2f}%")
            with col4:
                st.metric("Monthly Price Difference", f"${monthly_diff:.4f}", f"{percentage_difference_monthly:+.2f}%")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("90 Days Price Difference", f"${days_90_diff:,.4f}", f"{percentage_difference_days_90:+.2f}%")
            with col2:
                st.metric("6 Months Price Difference", f"${months_6_diff:,.4f}", f"{percentage_difference_months_6:+.2f}%")
            with col3:
                st.metric("52-Week High", f"${max_52_week_high:,.4f}")
            with col4:
                st.metric("52-Week Low", f"${min_52_week_low:,.4f}")

            st.subheader(chart_type)
            chart_data = go.Figure()

            if chart_type == "Candlestick Chart":
                chart_data.add_trace(go.Candlestick(
                    x=stock_data.index,
                    open=stock_data['Open'],
                    high=stock_data['High'],
                    low=stock_data['Low'],
                    close=stock_data['Close'],
                    showlegend=False  # Hide the legend for the candlestick chart
                ))

            # Get regression values and bands
            regression_values, bands, degree = calculate_regression_curve(stock_data.index, stock_data['Close'], degree)
            # Add regression curve trace
            chart_data.add_trace(go.Scatter(
                x=stock_data.index,
                y=regression_values,
                mode='lines',
                name='Regression Curve',
                line=dict(color='orange', width=2),
                showlegend=False
            ))

            for i, (lower_band, upper_band, color, (upper_text, upper_color, lower_text, lower_color)) in enumerate(bands):
                chart_data.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=upper_band,
                    mode='lines',
                    name='Take Profit Zones',
                    line=dict(color=color, width=1),
                    showlegend=False
                ))

                chart_data.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=lower_band,
                    mode='lines',
                    name='DCA Buy Zones',
                    line=dict(color=color, width=1),
                    showlegend=False
                ))

                # Add annotations for each band
                annotation_offset = 0.15 * len(stock_data)
                annotation_x = stock_data.index[-1] + pd.DateOffset(days=annotation_offset)

                # Upper band annotation
                chart_data.add_annotation(
                    x=annotation_x,
                    y=upper_band[-1],
                    text=upper_text,
                    font=dict(color=upper_color, size=12),
                    showarrow=False
                )

                # Lower band annotation
                chart_data.add_annotation(
                    x=annotation_x,
                    y=lower_band[-1],
                    text=lower_text,
                    font=dict(color=lower_color, size=12),
                    showarrow=False
                )

            if chart_type == "Line Chart":
                chart_data.add_trace(go.Scatter(
                    x=stock_data.index,
                    y=stock_data['Close'],
                    mode='lines',
                    name='Close Price',
                    line=dict(color='blue', width=1),
                    showlegend=False
                ))

            chart_data.update_layout(title=f"{symbol} - {chart_type}",
                                      xaxis_rangeslider_visible=False,
                                      yaxis=dict(title="Price", tickprefix="$"),
                                      xaxis_title="")
            st.plotly_chart(chart_data, use_container_width=True)

            st.subheader("Summary")
            st.dataframe(stock_data.tail(30))  # Display the last 30 days of data in max width


        # Refresh the app every 5 minutes
        time.sleep(60)
        st.rerun()

if __name__ == "__main__":
    app()
