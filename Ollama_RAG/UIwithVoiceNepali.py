
import ollama
import streamlit as st
import time
import os
from datetime import datetime
import json
import asyncio
from gtts import gTTS
import os
import pygame

import speech_recognition as sr
import pyttsx3
from io import BytesIO
from pocketsphinx import AudioFile, Pocketsphinx, get_model_path
import tempfile
from googletrans import Translator

# Initialize translator
translator = Translator()

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Initialize text-to-speech engine
#tts_engine = pyttsx3.init()

def response_generator(msg_content):
    lines = msg_content.split('\n')  # Split the content into lines to preserve paragraph breaks.
    for line in lines:
        words = line.split()  # Split the line into words to introduce a delay for each word.
        for word in words:
            yield word + " "
            time.sleep(0.1)
        yield "\n"  # After finishing a line, yield a newline character to preserve paragraph breaks.

def show_msgs():
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            # For assistant messages, use the custom avatar
            with st.chat_message("assistant"):
                st.write(msg["content"])
        else:
            # For user messages, display as usual
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

def chat(message, model='llama3.2'): ### CHANGE MODEL ID HERE 
    try:
        system_message = {
            'role': 'system',
            'content': (
                """You are Karishma Rana, a helpful receptionist for Infomax College, Pokhara, Nepal. 
                Answer questions concisely and professionally about the college. Never ask the user questions unless 
                explicitly prompted to do so. Always behave as an assistant. You just need to introduce yourself and write your 
                name and position once in the beginning.

                Some information about Infomax College for your information:

                Situated in the heart of Pokhara, Infomax College of IT & Management is one of the 
                pioneers of IT and Management education in and around Pokhara valley.

                Founded by IT Professionals, when the IT industry was in the beginning stage and there were 
                no Market oriented Management program.

                As an academic institution, we are dedicated to fostering innovation and entrepreneurship 
                where we encourage our students to think critically, embrace creativity, and pursue their passions by 
                ensuring our students are well prepared for the professional world.

                Our state of art facilities, cutting edge laboratories, open and spacious buildings covered with lush greenery, 
                where you can pause, breathe in the fresh air, and immerse yourself in the tranquility of surroundings.

                **Founder of Infomax College: Bikash Pahari, Birth place: Lakeside, Pokhara

                **Principal: Sushil Adhikari, Birth place:  Bindabasini, Pokhara

                **Creator of this application: Rajeev Poudel, Birth place: Bhalam, Pokhara

                **Prem Shrestha: Senior Lecturer in Infomax, currently living in Fulbari, Pokhara.

                **Administrative Head: Kamana Poudel, Quality: She is very hardworking lady. 

                Courses offered:
                1) BSc IT (3 years with 6 semesters)
                **First Semester courses:
                -Introduction to Database
                -Introduction to Networking
                -Introduction to C Programming
                -Mathematical Concepts for Computing
                -Nepal Parichaya
                -System Analysis and Design

                **Second Semester courses:
                -Intercultural Awareness and Cultural Diversity
                -Operating Systems & Computer Architecture
                -Fundamentals of Web Design and Development
                -Digital Thinking and Innovation
                -Programming with Python
                -Personality Development
                -Technical Communication

                **Third Semester Courses:
                -System Development Methods
                -Object Oriented Development with Java
                -Probability and Statistical Modelling
                -Creativity & Innovation
                -Mobile and Wireless Technology
                -System and Network Administration
                -Employees and Employment Trends

                **Fourth Semester Courses:
                -Programming for Data Analysis
                -Human Computer Interaction
                -Research Methods for Computing and Technology
                -Web Applications
                -Data Centre Infrastructure
                -Workplace Professional Communication Skills
                -Integrated Business Processes with SAP ERP

                **Fifth Semester Courses:
                -Distributed Computer Systems
                -Project Management
                -Investigations Module
                -Cloud Infrastructure and Services
                -Computer Systems Management
                -Mobile and Web Multimedia
                -Internship

                **Sixth Semester Courses:
                -Innovation Management & New Product Development
                -Entrepreneurship
                -Final Year Project
                -Advanced Database System
                -Designing and Developing Applications on the Cloud


                2) MBA (2 years with 4 semesters ):
                **Program Head and Coordinator: Arjun Sigdel, Birth Place: Kudhahar, Pokhara

                Contact Details:
                Location: Ranipauwa, Fulbari Marga, Pokhara-11
                Contact Number: 00977-61-585735 , 9846294602
                Email: info@infomaxcollege.edu.np
                
                
                """
            ),
        }

        # Combine the system message with the conversation history
        conversation = [system_message] + st.session_state.messages+ [{'role': 'user', 'content': message}]

        # Send the conversation to the model
        response = ollama.chat(model=model, messages=conversation)

        return response['message']['content']
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return f"Model '{model}' not found. Please refer to Doumentation at https://ollama.com/library."
        else:
            return f"An unexpected error occurred with model '{model}': {str(e)}"
        

def format_messages_for_summary(messages):
    # Create a single string from all the chat messages
    return '\n'.join(f"{msg['role']}: {msg['content']}" for msg in messages)

def summary(message, model='llama3.2'):
    sysmessage = "Summarize this conversation in 3 words. No symbols or punctuation:\n\n\n"
    api_message = sysmessage + message
    try:
        response = ollama.chat(model=model, messages=[
            {
                'role': 'user',
                'content': api_message,
            }
        ])
        return response['message']['content']
    except Exception as e:
        error_message = str(e).lower()
        if "not found" in error_message:
            return f"Model '{model}' not found. Please refer to Documentation at https://ollama.com/library."
        else:
            return f"An unexpected error occurred with model '{model}': {str(e)}"

def save_chat():
    if not os.path.exists('./Chats'):
        os.makedirs('./Chats')
    if st.session_state['messages']:
        formatted_messages = format_messages_for_summary(st.session_state['messages'])
        chat_summary = summary(formatted_messages)
        filename = f'./Chats/{chat_summary}.txt'
        with open(filename, 'w') as f:
            for message in st.session_state['messages']:
                # Replace actual newline characters with a placeholder
                encoded_content = message['content'].replace('\n', '\\n')
                f.write(f"{message['role']}: {encoded_content}\n")
        st.session_state['messages'].clear()
    else:
        st.warning("No chat messages to save.")

def load_saved_chats():
    chat_dir = './Chats'
    if os.path.exists(chat_dir):
        # Get all files in the directory
        files = os.listdir(chat_dir)
        # Sort files by modification time, most recent first
        files.sort(key=lambda x: os.path.getmtime(os.path.join(chat_dir, x)), reverse=True)
        for file_name in files:
            display_name = file_name[:-4] if file_name.endswith('.txt') else file_name  # Remove '.txt' from display
            if st.sidebar.button(display_name):
                st.session_state['show_chats'] = False  # Make sure this is a Boolean False, not string 'False'
                st.session_state['is_loaded'] = True
                load_chat(f"./Chats/{file_name}")
                # show_msgs()

def format_chatlog(chatlog):
    # Formats the chat log for downloading
    return "\n".join(f"{msg['role']}: {msg['content']}" for msg in chatlog)

def load_chat(file_path):
    # Clear the existing messages in the session state
    st.session_state['messages'].clear()  # Using clear() to explicitly empty the list
    show_msgs()
    # Read and process the file to extract messages and populate the session state
    with open(file_path, 'r') as file:
        for line in file.readlines():
            role, content = line.strip().split(': ', 1)
            # Decode the placeholder back to actual newline characters
            decoded_content = content.replace('\\n', '\n')
            st.session_state['messages'].append({'role': role, 'content': decoded_content})

def recognize_speech():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("Listening... Please speak.")
        try:
            audio = recognizer.listen(source, timeout=15)
            st.info("Processing audio...")
            return recognizer.recognize_google(audio)
        except sr.UnknownValueError:
            return "Sorry, I couldn't understand the audio."
        except sr.RequestError as e:
            return f"Could not request results; {e}"

def listen_for_speech(prompt=None, keyword=None, language="ne-NP"):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if prompt:
            print(prompt)
        recognizer.adjust_for_ambient_noise(source)
        st.info("Listening... Please speak.")
        audio = recognizer.listen(source, timeout=15)

    try:
        # Recognize speech in the specified language
        text = recognizer.recognize_google(audio, language=language)
        print(f"Recognized: {text}")
        if keyword:
            return keyword.lower() in text.lower()
        return text
    except sr.UnknownValueError:
        print("Could not understand the audio")
        return False if keyword else ""
    except sr.RequestError:
        print("Could not request results from speech recognition service")
        return False if keyword else ""


# def recognize_speech_offline():
#     try:
#         st.info("Listening... Please speak.")
        
#         # Initialize a temporary audio file to store input
#         recognizer = sr.Recognizer()
#         with sr.Microphone() as source:
#             audio_data = recognizer.listen(source)
        
#         # Save the audio data to a temporary WAV file
#         with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio_file:
#             temp_audio_file.write(audio_data.get_wav_data())
#             temp_audio_path = temp_audio_file.name
        
#         # Define PocketSphinx configuration
#         model_path = get_model_path()
#         config = {
#             'hmm': os.path.join(model_path, 'en-us'),
#             'lm': os.path.join(model_path, 'en-us.lm.bin'),
#             'dict': os.path.join(model_path, 'cmudict-en-us.dict'),
#         }
        
#         # Recognize speech from the temporary WAV file
#         ps = Pocketsphinx(**config)
#         ps.decode(audio_file=temp_audio_path)
        
#         # Return the recognized text
#         recognized_text = ps.hypothesis()
#         if not recognized_text:
#             return "Sorry, I couldn't understand the audio."
#         return recognized_text
#     except Exception as e:
#         st.error(f"Error in offline speech recognition: {str(e)}")
#         return "Error in processing audio."

def speak_text(text, language="en-US"):
    # Convert text to audio and play it
    try:
        # Use pyttsx3 to convert text to speech and play it directly
        #tts_engine.save_to_file(text, "response.mp3")
        # Initialize a new TTS engine for each call
        tts_engine = pyttsx3.init()
        tts_engine.say(text)
        tts_engine.runAndWait()

        # Safely terminate the engine to avoid conflicts
        tts_engine.stop()
    except Exception as e:
        st.error(f"Error in playing voice response: {str(e)}")
    # audio = AudioSegment.from_file("response.mp3", format="mp3")
    # play(audio)

async def translate_text(text, dest_lang):
    async with Translator() as translator:

        translated_text = (await translator.translate(text, dest=dest_lang)).text
    
    return translated_text


def text_to_speech(text, lang='ne'):
    tts = gTTS(text=text, lang=lang)
    tts.save("response.mp3")
    
    pygame.mixer.music.load("response.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    
    pygame.mixer.music.unload()  # Unload the music to release the file
    
    # Attempt to delete the file after it is no longer in use
    try:
        os.remove("response.mp3")
    except PermissionError:
        print("Error: Unable to delete 'response.mp3'. Retrying...")
        time.sleep(1)
        try:
            os.remove("response.mp3")
        except Exception as e:
            print(f"Failed to delete 'response.mp3': {e}")

def main():
    st.title("Infomax GPT")
    user_input = st.chat_input("Enter your prompt:", key="1")
    
    if 'show' not in st.session_state:
        st.session_state['show'] = 'True'
    if 'show_chats' not in st.session_state:
        st.session_state['show_chats'] = 'False'
    if 'messages' not in st.session_state:
        st.session_state['messages'] = []
    show_msgs()
     # Button to enable voice input
    
    if st.button("Use Voice Input"):
        #voice_message = recognize_speech()
        voice_message_nepali = listen_for_speech(prompt="Listening",language="ne-NP")
        voice_message = asyncio.run(translate_text(voice_message_nepali, "en"))
        print(voice_message)
        if voice_message:
            with st.chat_message("user"):
                st.write(voice_message)
                
            st.session_state.messages.append({"role": "user", "content": voice_message})
            response = chat(voice_message)
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.write_stream(response_generator(response))
                #speak_text(response)
                nepali_response = asyncio.run(translate_text(response, "ne"))
                #print(nepali_response)
                #speak_text(nepali_response)
                text_to_speech(nepali_response)

    if user_input:
        with st.chat_message("user"):
            st.write(user_input)
            #speak_text("The question asked is:"+ voice_message)
        st.session_state.messages.append({"role": "user", "content": user_input})
        messages = "\n".join(msg["content"] for msg in st.session_state.messages)
        # print(messages)
        response = chat(messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.write_stream(response_generator(response))
            nepali_response = asyncio.run(translate_text(response, "ne"))
            #print(nepali_response)
            #speak_text(nepali_response)
            text_to_speech(nepali_response)

    elif st.session_state['messages'] is None:
        st.info("Enter a prompt or load chat above to start the conversation")
    chatlog = format_chatlog(st.session_state['messages'])
    st.sidebar.download_button(
        label="Download Chat Log",
        data=chatlog,
        file_name="chat_log.txt",
        mime="text/plain"
    )
    for i in range(5):
        st.sidebar.write("")
    if st.sidebar.button("Save Chat"):
        save_chat()

    
    # Show/Hide chats toggle
    if st.sidebar.checkbox("Show/hide chat history", value=st.session_state['show_chats']):
        st.sidebar.title("Previous Chats")
        load_saved_chats()
        
    for i in range(3):
        st.sidebar.write(" ")
    

if __name__ == "__main__":
    main()
    pygame.mixer.quit()