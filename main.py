from mistralai import Mistral
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import json


load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
cse_id = os.getenv("CSE_ID")

api_key = os.getenv("MISTRAL_API_KEY")
model = "mistral-small-latest"
client = Mistral(api_key=api_key)

TRUNCATE_SCRAPED_CONTENT = 75000
SEARCH_DEPTH = 5

tools = [
    {
        "type": "function",
        "function": {
            "name": "retrieve_web_results",
            "description": "Perform a web search based on a user prompt and return summarized search results written to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "The user-provided prompt to generate a search query and retrieve web results"
                    }
                },
                "required": ["prompt"]
            }
        }
    }
]


def web_search(search_item, api_key, cse_id, search_depth=10, site_filter=None):
    service_url = "https://www.googleapis.com/customsearch/v1"

    params = {"q": search_item, "key": api_key, "cx": cse_id, "num": search_depth}

    try:
        response = requests.get(service_url, params=params)
        response.raise_for_status()
        results = response.json()

        if "items" in results:
            if site_filter is not None:

                filtered_results = [
                    result
                    for result in results["items"]
                    if site_filter in result["link"]
                ]

                if filtered_results:
                    return filtered_results
                else:
                    print(f"No results with {site_filter} found.")
                    return []
            else:
                if "items" in results:
                    return results["items"]
                else:
                    print("No search results found.")
                    return []

    except requests.exceptions.RequestException as e:
        print(f"An error occurred during the search: {e}")
        return []


def retrieve_content(url, max_tokens=TRUNCATE_SCRAPED_CONTENT):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")
        for script_or_style in soup(["script", "style"]):
            script_or_style.decompose()

        text = soup.get_text(separator=" ", strip=True)
        characters = max_tokens * 4
        text = text[:characters]
        return text
    except requests.exceptions.RequestException as e:
        print(f"Failed to retrieve {url}: {e}")
        return None


def summarize_content(content, search_term, character_limit=500):
    prompt = (
        f"You are an AI assistant tasked with summarizing content relevant to '{search_term}'. "
        f"Please provide a concise summary in {character_limit} characters or less."
    )
    try:
        messages = [
            {"role": "system", "content": [{"type": "text", "text": prompt}]},
            {"role": "user", "content": [{"type": "text", "text": content}]},
        ]

        chat_response = client.chat.complete(model=model, messages=messages)
        return chat_response.choices[0].message.content
    except Exception as e:
        print(e)
        return None


def get_search_results(search_items, search_item, character_limit=500):
    results_list = []
    for idx, item in enumerate(search_items, start=1):
        url = item.get("link")

        snippet = item.get("snippet", "")
        web_content = retrieve_content(url, TRUNCATE_SCRAPED_CONTENT)

        if web_content is None:
            print(f"Error: skipped URL: {url}")
        else:
            summary = summarize_content(
                web_content, search_item, character_limit
            )
            result_dict = {
                "order": idx,
                "link": url,
                "title": snippet,
                "Summary": summary,
            }
            results_list.append(result_dict)
    return results_list



def retrieve_web_results(prompt: str) -> str:
    try:
        search_query = (
            client.chat.complete(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "content": "text",
                                "text": "Extract the core topic from the user prompt and generate a single, concise Google search term (2-4 words) without quotes, specific phrases, or technical jargon. Use broad, general keywords to ensure relevant web results.",
                            }
                        ],
                    },
                    {"role": "user", "content": [{"type": "text", "text": prompt}]},
                ],
            )
            .choices[0]
            .message.content
        )
        print(f"Search Query: {search_query}")
        raw_result = web_search(search_query, google_api_key, cse_id)
        # print(f"Raw result: {raw_result}")
        result = get_search_results(raw_result, search_query)
        # print(f"Result: {result}")

        with open("web_results.md", "w", encoding="utf-8") as f:
            for item in result:
                try:
                    f.write(f"Search order: {item['order']}\n")
                    f.write(f"Link: {item['link']}\n")
                    f.write(f"Snippet: {item['title']}\n")
                    f.write(f"Summary: {item['Summary']}\n")
                    f.write("-" * 80 + "\n")
                except KeyError as e:
                    print(f"Warning: Skipping item due to missing key: {e}")

        with open("web_results.md", "r", encoding="utf-8") as f:
            file_content = f.read()

        return file_content

    except Exception as e:
        print(f"An error occurred: {e}")
        return f"Error: {str(e)}"


names_to_function = {
    'retrieve_web_results': retrieve_web_results
}

def main():
    try:
        prompt = input('User Prompt: ')
        synthesis_system_prompt = f"""You are an AI assistant. **IF** you take help of web search results, follow the instructions below. 
        The search results are formatted as follows for each item:
        Search order: [number]
        Link: [URL of the source]
        Title: [Title of the webpage]
        Summary: [AI-generated summary of the content]
        --------------------------------------------------------------------------------

        When you use information from a search result, you MUST cite the source immediately after the information.
        Use Markdown link format for citations. The citation should use the actual 'Link' (URL) from the search result.

        For example, if you use information from a result with "Link: http://example.com/article1", your citation should look like:
        "This information comes from the web. [Source](http://example.com/article1)"
        Or, if you are summarizing a point: "According to the search results, the sky is blue. [Learn more](http://example.com/source-link)"

        **Crucial Instructions for Citation:**
        1.  **DO NOT** use tags like `[REF]...[/REF]`, `[source N]`, or any other placeholder.
        2.  **ALWAYS** use the direct URL provided in the 'Link:' field of the search result for the citation.
        3.  The citation should be a Markdown link: `[Visible Text](URL)`. You can use text like "Source", "Details", the title of the page, or a brief description as the `Visible Text`.
        4.  If multiple search results contribute to a single point, you can list multiple citations.
        5.  If the search results do not contain information to answer the query, clearly state that.
        6.  Synthesize the information from the summaries provided. Do not invent information.
        """
        messages = [{
            "role":"system",
            "content": synthesis_system_prompt
        },
            {
                "role": "user",
                "content": [{
                    "type": "text",
                    "text": prompt
                }]
            }
        ]
        response = client.chat.complete(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            parallel_tool_calls=False
        )

        messages.append(response.choices[0].message)

        if not response.choices[0].message.tool_calls:
            print("No tool calls in response.")
            with open("output.md", "w", encoding="utf-8") as f:
                f.write(response.choices[0].message.content)
            return

        tool_call = response.choices[0].message.tool_calls[0]
        function_name = tool_call.function.name
        function_params = json.loads(tool_call.function.arguments)
        print(f"Function name: {function_name}\nFunction params: {function_params}")
        function_result = names_to_function[function_name](**function_params)

        messages.append({
            "role":"tool", 
            "name":function_name, 
            "content":function_result, 
            "tool_call_id":tool_call.id
        })

        # print(f"Messages: {messages}")
        # print(function_result)

        response = client.chat.complete(
            model=model,
            messages=messages
        )
        
        with open("output.md", "w") as f:
            f.write(response.choices[0].message.content)

        print("Output pasted in output.md file!")
        

    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()
