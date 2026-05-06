import google.generativeai as genai

# Configuration
# IMPORTANT: Replace 'YOUR_API_KEY' with your actual Google API key
GOOGLE_API_KEY = 'AIzaSyBlVI2kmEOTN1xibPMmRrQCSK-0OVLfLtA'

def main():
    """The main function that runs the AI assistant."""
    try:
        # Configure generative AI model
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel(model="gpt-mini-1.0-pro")
        chat = model.start_chat(history=[])

        # Print welcome message
        print("\n--- K-Tech AI Assistant ---")
        print("Status: Initializing...")
        print("Status: AI Model Initialized. Ready to chat.")

        # Main chat loop
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("Exiting...")
                break
            response = chat.send_message(user_input)
            print("Assistant:", response['text'])

    except Exception as e:
        print("An error occurred:", e)

if __name__ == "__main__":
    main()