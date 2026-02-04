import os
from flask import Flask, request, url_for, send_from_directory, render_template
import plivo
from plivo.xml import (
    ResponseElement as Response,
    GetDigitsElement as GetDigits,
    SpeakElement as Speak,
    PlayElement as Play,
    DialElement as Dial,
    NumberElement as Number,
    RedirectElement as Redirect
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
PLIVO_AUTH_ID = os.getenv("PLIVO_AUTH_ID")
PLIVO_AUTH_TOKEN = os.getenv("PLIVO_AUTH_TOKEN")
PLIVO_PHONE_NUMBER = os.getenv("PLIVO_PHONE_NUMBER") # The number acting as caller ID
NGROK_URL = os.getenv("NGROK_URL") # Public URL for webhooks

# Initialize Plivo Client
client = plivo.RestClient(PLIVO_AUTH_ID, PLIVO_AUTH_TOKEN)

# Placeholder Associate Number (Demo)
ASSOCIATE_NUMBER = "14692463990" 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/initiate_call', methods=['GET', 'POST'])
def initiate_call():
    """
    Initiates an outbound call to the specified number.
    Usage: /initiate_call?to=1234567890
    """
    to_number = request.args.get('to') or request.form.get('to')
    
    if not to_number:
        return "Error: Missing 'to' parameter (target phone number).", 400

    if not NGROK_URL:
        return "Error: NGROK_URL not set in environment.", 500

    try:
        # The answer_url is the webhook Plivo calls when the user answers
        answer_url = f"{NGROK_URL}/ivr/level1"
        
        response = client.calls.create(
            from_=PLIVO_PHONE_NUMBER,
            to_=to_number,
            answer_url=answer_url,
            answer_method='POST'
        )
        return f"Call initiated! UUID: {response.request_uuid}"
    except Exception as e:
        return f"Failed to initiate call: {str(e)}", 500

# --- IVR LEVEL 1: Language Selection ---
@app.route('/ivr/level1', methods=['GET', 'POST'])
def ivr_level1():
    """
    Level 1 Menu: Select Language.
    """
    resp = Response()
    
    # GetDigits to capture input
    get_digits = GetDigits(
        action=f"{NGROK_URL}/ivr/level2_handler",
        method='POST',
        timeout=10, # Increased timeout for better UX
        num_digits=1,
        retries=3,
        redirect=True 
    )
    
    get_digits.add(Speak("Welcome to Inspire Works. Press 1 for English. Press 2 for Spanish."))
    
    resp.add(get_digits)
    resp.add(Speak("Sorry, we didn't receive any input. Goodbye."))
    
    xml_str = resp.to_string()
    print(f"DEBUG XML /ivr/level1:\n{xml_str}")
    
    return app.response_class(xml_str, mimetype='application/xml')

# --- IVR LEVEL 2 HANDLER: Route based on Language ---
@app.route('/ivr/level2_handler', methods=['POST'])
def ivr_level2_handler():
    """
    Handles input from Level 1 and directs to Level 2 Menu.
    """
    digit = request.form.get('Digits')
    print(f"DEBUG: Level 1 Input Received: {digit}")
    
    if digit == '1':
        return ivr_level2_menu(language="english")
    elif digit == '2':
        return ivr_level2_menu(language="spanish")
    else:
        resp = Response()
        resp.add(Speak("Invalid selection."))
        resp.add(Redirect(f"{NGROK_URL}/ivr/level1"))
        return app.response_class(resp.to_string(), mimetype='application/xml')

def ivr_level2_menu(language):
    resp = Response()
    
    action_url = f"{NGROK_URL}/ivr/action_handler?lang={language}"
    
    get_digits = GetDigits(
        action=action_url,
        method='POST',
        timeout=5,
        num_digits=1,
        retries=3
    )
    
    if language == "english":
        get_digits.add(Speak("Menu Level Two. Press 1 to play a message. Press 2 to talk to an associate."))
    else:
        get_digits.add(Speak("Menú Nivel Dos. Presione 1 para escuchar un mensaje. Presione 2 para hablar con un asociado.", language="es-US"))
        
    resp.add(get_digits)
    resp.add(Speak("No input received. Goodbye."))
    
    xml_str = resp.to_string()
    print(f"DEBUG XML Level 2 ({language}):\n{xml_str}")
    
    return app.response_class(xml_str, mimetype='application/xml')

# --- IVR ACTION HANDLER ---
# --- IVR ACTION HANDLER ---
@app.route('/ivr/action_handler', methods=['POST'])
def ivr_action_handler():
    """
    Handles input from Level 2 and executes action.
    """
    digit = request.form.get('Digits')
    language = request.args.get('lang', 'english')
    print(f"DEBUG: Action Input Received: {digit} (Lang: {language})")
    
    resp = Response()
    
    if digit == '1':
        # Action: Play Audio
        audio_url = f"{NGROK_URL}/public/audio/{language}.mp3"
        print(f"DEBUG: Playing audio from {audio_url}")
        resp.add(Play(audio_url))
        resp.add(Speak("Thank you for listening. Goodbye."))
        
    elif digit == '2':
        # Action: Forward to Associate
        resp.add(Speak("Connecting you to an associate now."))
        dial = Dial()
        dial.add(Number(ASSOCIATE_NUMBER))
        resp.add(dial)
        
    else:
        return ivr_level2_retry(language)

    xml_str = resp.to_string()
    print(f"DEBUG XML Action:\n{xml_str}")
    return app.response_class(xml_str, mimetype='application/xml')

def ivr_level2_retry(language):
    resp = Response()
    resp.add(Speak("Invalid selection. Please try again."))
    
    # Re-display Level 2 options
    action_url = f"{NGROK_URL}/ivr/action_handler?lang={language}"
    get_digits = GetDigits(action=action_url, method='POST', timeout=5, num_digits=1, retries=3)
    
    if language == "english":
        get_digits.add(Speak("Press 1 to play a message. Press 2 to talk to an associate."))
    else:
        get_digits.add(Speak("Presione 1 para escuchar un mensaje. Presione 2 para hablar con un asociado.", language="es-US"))
    
    resp.add(get_digits)
    
    return app.response_class(resp.to_string(), mimetype='application/xml')


# --- Serve Static Audio ---
@app.route('/public/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
