# Perfect AI Assistant

A sophisticated chat application built with Streamlit and Azure OpenAI, featuring multiple chat sessions, customizable AI behavior, and persistent message storage.

## Features

- 💬 Multiple chat sessions management
- 🔄 Real-time streaming responses
- 💾 Persistent message storage using SQLite
- ⚙️ Customizable system prompts
- 🎯 Specialized AI behavior templates
- 🔒 Secure credential management
- 🎨 Clean and intuitive user interface

## Prerequisites

- Python 3.8 or higher
- Azure OpenAI Service subscription
- Azure OpenAI API access

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd chat_app
```

2. Install required packages:

```bash
pip install -r requirements.txt
```

## Azure OpenAI Setup

1. Create an Azure OpenAI resource in the [Azure Portal](https://portal.azure.com)

2. Get your Azure OpenAI credentials:

   - Go to your Azure OpenAI resource
   - Navigate to "Keys and Endpoint" section
   - Note down:
     - Endpoint URL
     - API Key
     - API Version
     - Deployment Name

3. Create a `.env` file in the project root with your Azure OpenAI credentials:

```env
AZURE_OPENAI_CHAT_ENDPOINT=<your-endpoint-url>
AZURE_OPENAI_CHAT_API_KEY=<your-api-key>
AZURE_OPENAI_CHAT_API_VERSION=<api-version>  # e.g., 2023-05-15
AZURE_OPENAI_CHAT_DEPLOYMENT=<deployment-name>
```

## Running the Application

1. Start the Streamlit app:

```bash
streamlit run app.py
```

2. Open your browser and navigate to the provided URL (typically http://localhost:8501)

## Usage

1. **Chat Sessions**

   - Create new chat sessions using the "New Chat" button
   - Switch between existing chats in the sidebar
   - Delete unwanted chat sessions

2. **System Prompt Templates**

   - Choose from predefined AI behavior templates:
     - General Assistant
     - Healthcare Professional
     - Physiotherapy Expert
     - Software Developer
     - Business Consultant
     - Education Tutor

3. **Chat Interface**
   - Type your message in the input field
   - View real-time streaming responses
   - Access chat history for all sessions

## Database

The application uses SQLite for storing:

- Chat sessions
- Message history
- Timestamps for all interactions

## Security Notes

- Never commit your `.env` file to version control
- Keep your Azure OpenAI API keys secure
- Regularly rotate your API keys
- Monitor your Azure OpenAI usage
