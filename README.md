# LLM-websearch
A tool to let language models search the web using simple prompts.

Web Search Results             |  Final Output
:-------------------------:|:-------------------------:
![](https://github.com/user-attachments/assets/5dd85760-03ed-468e-ae05-53d4355f08bb)  |  ![](https://github.com/user-attachments/assets/9a87bd2f-17e6-4479-b2b0-2b0936b65117)


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
