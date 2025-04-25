# FinRobot Chatbot

A financial chatbot with UI built using the FinRobot model.

## Overview

This chatbot leverages the FinRobot financial AI model to provide financial analysis, investment advice, and market insights through a user-friendly web interface built with Streamlit.

## Features

- Interactive chat interface for financial queries
- Multiple financial agent profiles to choose from:
  - Expert Investor
  - Market Analyst
  - Financial Analyst
  - Data Analyst
  - AI Engineer
- Customizable response creativity with temperature slider
- Real-time financial data analysis

## Setup and Installation

1. **Install required packages**:
   ```
   pip install -r chatbot_requirements.txt
   ```

2. **API Key Setup**:
   - You'll need openAI api key for running this chatbot on your system.
   - For production deployment, use environment variables or Streamlit secrets

3. **Run the chatbot**:
   ```
   streamlit run finrobot_chatbot.py
   ```

## Usage

1. Select an agent profile from the sidebar
2. Adjust the temperature slider for response creativity
3. Click "Initialize Agent" to set up the agent
4. Type your financial question in the text area
5. Click "Send" to get a response

## Example Queries

- "What's your analysis of AAPL's recent performance?"
- "Can you give me investment advice for tech stocks in 2025?"
- "Analyze NVDA's financial statements and provide insights"
- "What are the market trends for renewable energy stocks?"
- "Create a basic investment portfolio for a risk-averse investor"

## Technical Details

The chatbot is built with:
- Streamlit for the user interface
- Autogen for the agent framework
- FinRobot financial models for analysis
- OpenAI's GPT models for natural language understanding

## License

See the project license file for details.
