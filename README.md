# LLM-websearch
A tool to let language models search the web using simple prompts.

Web Search Results             |  Final Output
:-------------------------:|:-------------------------:
 ![Screenshot 2025-06-05 161342 (Small) (1)](https://github.com/user-attachments/assets/47c56e00-73b3-43a7-b277-28963511979a)  |  ![Screenshot 2025-06-05 161350 (Small)](https://github.com/user-attachments/assets/862172a0-8be4-4a89-8c25-fe2036276375)



## Setup
1. Clone the repo:
   ```bash
   git clone https://github.com/your-username/LLM-WebSearch.git
   cd LLM-WebSearch

## Install packages:
`pip install mistralai requests beautifulsoup4 python-dotenv`


## Add API keys to a .env file:
```env
  GOOGLE_API_KEY=your-key
  CSE_ID=your-cse-id
  MISTRAL_API_KEY=your-mistral-key
```
## Usage
Run the script:`python main.py`<br>
See results in `output.txt` and answer in `web_results.md`.
