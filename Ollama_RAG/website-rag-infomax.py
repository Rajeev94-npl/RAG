import os
import json
import asyncio
import random
from ollama import AsyncClient
import requests 
from bs4 import BeautifulSoup
import time
import streamlit as st

website = ""

def response_generator(msg_content):
    lines = msg_content.split('\n')  # Split the content into lines to preserve paragraph breaks.
    for line in lines:
        words = line.split()  # Split the line into words to introduce a delay for each word.
        for word in words:
            yield word + " "
            time.sleep(0.1)
        yield "\n"  # After finishing a line, yield a newline character to preserve paragraph breaks.

async def scrape_website(url=website):
    try:
        # Send a GET request to the website
        response = requests.get(url)
        
        # If the GET request is successful, the status code will be 200
        if response.status_code == 200:
            # Get the content of the response
            page_content = response.content

            # Create a BeautifulSoup object and specify the parser
            soup = BeautifulSoup(page_content, 'html.parser')

            # Find all text on the webpage
            text = soup.get_text()

            return text
        else:
            print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

async def main():
    st.title("Infomax Website Assistant")
    # Load text
    website = st.chat_input("Enter the website of your college/school",key="1")

    if website:
        with st.spinner("Generating response...."):
            try:

                # Initialize Ollama client
                client = AsyncClient()

                # Define the functions (tools) for the model
                tools = [
                    {
                        "type": "function",
                        "function": {
                            "name": "scrape_website",
                            "description": "Fetch information about the college",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "url": {
                                        "type": "string",
                                        "description": f"{website}",
                                    },
                                },
                                "required": ["url"],
                            },
                        },
                    }
                ]

                # Step 1: Categorize items using the model
                categorize_prompt = f"""
            You are an assistant that answers the questions about the college.

            **Instructions:**

            - Return the answer in precise and short form with different important categories like name, location, programs offered, principal/founder name, Alumni, Contact Number, short summary of the institution etc.
            Also, please add some spacing between the different headings. 

            """

                messages = [{"role": "user", "content": categorize_prompt}]
                # First API call: Categorize items
                response = await client.chat(
                    model="llama3.2",
                    messages=messages,
                    tools=tools,  # No function calling needed here, but included for consistency
                )

                # Add the model's response to the conversation history
                messages.append(response["message"])
                print(response["message"]["content"])

                # Parse the model's response
                assistant_message = response["message"]["content"]

                # Step 2: Fetch college info

                # Construct a message to instruct the model to fetch college info

                fetch_prompt = """
                Use the 'scrape_website' function to get information about the college.
                """

                messages.append({"role": "user", "content": fetch_prompt})

                # Second API call: The model should decide to call the function for each item
                response = await client.chat(
                    model="llama3.2",
                    messages=messages,
                    tools=tools,
                )
                # Add the model's response to the conversation history
                messages.append(response["message"])

                # Process function calls made by the model
                if response["message"].get("tool_calls"):
                    print("Function calls made by the model:")
                    available_functions = {
                        "scrape_website": scrape_website
                    }
                    # Store the details for later use
                    item_details = []
                    for tool_call in response["message"]["tool_calls"]:
                        function_name = tool_call["function"]["name"]
                        arguments = tool_call["function"]["arguments"]
                        function_to_call = available_functions.get(function_name)
                        if function_to_call:
                            result = await function_to_call(**arguments)
                            # Add function response to the conversation
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": result.strip(),
                                }
                            )
                            item_details.append(result)

                            #print(item_details)
                else:
                    print(
                        "The model didn't make any function calls for fetching information."
                    )
                    return

                # Final API call: Get the assistant's final response
                final_response = await client.chat(
                    model="llama3.2",
                    messages=messages,
                    tools=tools,
                )

                with st.chat_message("assistant"):
                    st.write_stream(response_generator(final_response["message"]["content"]))
                
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
    else:
        st.info("Please enter the website of your institution to get started!!!")

# Run the async main function
if __name__ == "__main__":
    asyncio.run(main())
