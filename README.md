# AlgoTrader

*A Python-based algorithmic trading bot designed to automate trading strategies in financial markets using **Plotly** and **Dash** for interactive data visualization.*


## Table of Contents

- 🚧 Project Status
- 📥 Installation
- 📁 Project Structure
- 🚀 Quick Start
- 🌟 Features
- 🛣️ Roadmap
- 🎯 Basic Strategy Outline
- 📄 License

## Project Status

🚧 Under Construction 🚧

This project is in the early stages, and many features are still being developed. Contributions and feedback are welcome!

## 📥 Installation

1. **Clone the repository**

    ```bash
    pip install git+https://github.com/vmichael89/AlgoTrader.git
   ```

    or

    ```bash
    git clone https://github.com/vmichael89/AlgoTrader.git```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
   ```

3. **Configure API keys**

    Add your API keys to `trader/config/` according to the example files

## 📁 Project Structure
```
AlgoTrader/
├── data/ 
├── tests/
├── trader/                 # Main trading application package
│   ├── algos/              # Trading algorithms and technical indicators
│   ├── config/             # API tokens
│   ├── risk_management/    # Risk management modules
│   ├── patterns/           # Chart pattern recognition modules
│   ├── strategies/         # Trading strategy implementations
│   ├── app.py  <--entry    # Dash application entry point
│   ├── broker.py           # Broker integration modules
│   └── trader.py           # Core trading logic
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
└── LICENSE                 # License information
```

## 🚀 Quick Start

Explore the features of AlgoTrader by running the main scripts directly. Since the project is still under development, it is not yet packaged for installation via `import trader`. Follow the steps below to get started quickly.

### 1. Run the Trader Script in Interactive Mode
Run `trader/trader.py` from its directory directly to play with its features
- Access all available instruments through the brokers `instruments` attribute
```python
trader = Trader()
trader.add_data(trader.broker.instruments.EUR_USD)
```

### 2. Experiment with Algorithms

Run `tests/test_directional_change.py` to see the current implementation of this algo

The `DirectionslChange` class has two methods to process information
- `.get_extremes(df, sigma)` stores all extremes in the attribute `.extreme`
- `.process_data_point(index, high, low)` acts on single price data meant for streaming data
- `.plot(ax)` plots the extremes to the specified axes, still using matplotlib as plotting backend 

### 3. Run the Dash Application for Visualization
Run `trader/app.py` from its directory directly to play with its features
- App will be hosted on http://127.0.0.1:8050/
- Every change to the traders data attribute will trigger a graph update
    - `trader.add_data()` easily adds new ohlc data to `trader.data` which adds a new plot
    - to update a single plot, e.g. for streaming, the data has to be changed

## 🌟 Features

- Fetch historical prices (data) from Oanda
- Add data to trader instance
- Display the trader's candlestick charts in a Dash web application
- Find local extremes using a directional change algo

## 🛣️ Roadmap

### Algorithms

- [ ] **Support and Resistance Levels**: Implement detection algorithms.
- [ ] **Local Extremes**: Improve existing algo and implement new ones (rolling window method, perceptional important points)
- [ ] **Fibonacci Retracements**: Include tools for retracement analysis.

### Pattern Recognition

- [ ] **Double tops and bottoms**
- [ ] **Head and shoulders**
- [ ] **Wedge patterns**
- [ ] **Rectangles (bearish and bullish)**
- [ ] **Triangle patterns**
- [ ] **Elliott waves**
- [ ] **Harmonic price patterns**

### Broker Integration

  - [ ] **Interactive Brokers integration (with ib-insync)**
  - [ ] **Non-account data sources (e.g., yfinance)**
  
### Risk Management

  - [ ] **Position Sizing Algorithms**: Calculate optimal trade sizes based on *risk tolerance*
  - [ ] **Maximum Drawdown Limit**: Set thresholds to halt trading after significant cumulative losses.
  - [ ] **Stop-Loss and Take-Profit Mechanisms including Price Spreads**
  - [ ] **Risk-to-Reward Ratio Enforcement**: Ensure trades meet minimum risk-to-reward criteria.
  - [ ] **Margin Monitoring**: Keep track of margin levels to prevent margin calls.
  - [ ] ...

### Trader Functionality  
  - [ ] **Real-Time Data Processing**: Use threading or asynchronous methods. 
  - [ ] **Backtesting Module**: Develop tools for historical strategy testing. 

### Dash Application Enhancements
  - [ ] **Real-Time Data Visualization**
  - [ ] **Interactive Charting**: Toggle visibility of indicators and features from above
  - [ ] **Backtesting Interface**: Develop an interface where users can select a strategy, set parameters, and run backtests directly from the web app
  - [ ] **Training Tool**: Simulate strategy and stop at decision points where the user can go long or short

## 🎯 Basic Strategy Outline

The goal of this trading strategy is to identify high-probability trade opportunities with a strong emphasis on risk management. The approach focuses on quality over quantity, accepting that fewer trades may be taken in favor of higher confidence setups. To maximize potential opportunities, the strategy involves screening as many instruments as possible.

### **1. Identify Potential Trade Entries**

- **Chart Pattern Formation**: Monitor multiple financial instruments for the formation of specific chart patterns known to indicate potential trading opportunities.

### **2. Assess Initial Risk/Reward Ratio**

- **Determine Possible Trade Exits**:

  - **Based on Chart Pattern Definition**: Identify exit points according to the expected completion of the chart pattern.
  - **Support and Resistance Levels**: Consider key support and resistance levels that may impact the trade.

- **Evaluate Risk Management Compatibility**:

  - **Risk/Reward Analysis**: Calculate the potential risk and reward of the trade using the identified entry and exit points.
  - **Risk Management Criteria**: Ensure the trade meets predefined risk management parameters, such as a minimum acceptable risk/reward ratio.

### **3. Confirm Chart Pattern**

- **Traditional Confirmation**: Wait for the price action to confirm the chart pattern according to standard technical analysis definitions.
- **Early Entry Using Technical Indicators (preferred)**: Employ candlestick patterns and technical indicators like RSI and DMI to predict if the chart pattern is likely to form.

### **4. Execute the Trade**

- **Entry Execution**: Proceed with the trade if all criteria are met.
- **Set Stop-Loss and Take-Profit Levels**: Use the levels identified in step 2 to manage risk.

### **5. Monitor and Exit Trade**

- **Pattern Completion**: Exit the trade when the price reaches the take-profit level or fulfills the chart pattern's projected move.
- **Emergency Exit**: Close the position if technical indicators or candlestick patterns suggest that the pattern is failing or reversing.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
