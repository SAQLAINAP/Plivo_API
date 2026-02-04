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
    retry = int(request.args.get('retry', 0))
    resp = Response()
    
    # GetDigits with manual retry handling (retries=0)
    # We pass the current retry count to the handler
    get_digits = GetDigits(
        action=f"{NGROK_URL}/ivr/level2_handler?retry={retry}",
        method='POST',
        timeout=7,
        num_digits=1,
        retries=0, 
        redirect=True 
    )
    
    get_digits.add(Speak("Welcome to Inspire Works. Press 1 for English. Press 2 for Spanish."))
    
    resp.add(get_digits)
    
    # If we get here, it means GetDigits timed out/failed in a way that didn't redirect (fallback)
    # But with redirect=True, it should hit the handler. 
    # Just in case, we add a fallback redirect/hangup logic here? 
    # Actually, Plivo executes the next element if no API trigger happening.
    # But redirect=True forces the API hit.
    
    # However, if no input is entered, GetDigits might fall through if redirect is NOT triggered 
    # (though docs say redirect=True trumps).
    # To be safe, we will let the handler catch the "No Input" case via the action URL.
    
    xml_str = resp.to_string()
    print(f"DEBUG XML /ivr/level1 (retry={retry}):\n{xml_str}")
    
    return app.response_class(xml_str, mimetype='application/xml')

# --- IVR LEVEL 2 HANDLER: Route based on Language ---
@app.route('/ivr/level2_handler', methods=['POST'])
def ivr_level2_handler():
    """
    Handles input from Level 1 and directs to Level 2 Menu.
    """
    digit = request.form.get('Digits')
    retry = int(request.args.get('retry', 0))
    print(f"DEBUG: Level 1 Input: '{digit}', Retry: {retry}")
    
    resp = Response()

    # Case 1: Valid Input
    if digit == '1':
        return ivr_level2_menu(language="english")
    elif digit == '2':
        return ivr_level2_menu(language="spanish")
    
    # Error Handling Logic
    if not digit:
        # Case 2: No Input (Timeout)
        message = "Nothing selected."
    else:
        # Case 3: Invalid Input (Wrong Digit)
        message = "Invalid selection."
    
    if retry < 1:
        # First Failure: Warn and Retry
        resp.add(Speak(f"{message} Please try again."))
        resp.add(Redirect(f"{NGROK_URL}/ivr/level1?retry=1"))
    else:
        # Second Failure: Goodbye and Cut
        resp.add(Speak("No response. Goodbye."))
        # Plivo will hangup automatically after xml ends, or we can explicit Hangup
    
    return app.response_class(resp.to_string(), mimetype='application/xml')

def ivr_level2_menu(language, retry=0):
    resp = Response()
    
    # Pass retry count to the action handler
    action_url = f"{NGROK_URL}/ivr/action_handler?lang={language}&retry={retry}"
    
    get_digits = GetDigits(
        action=action_url,
        method='POST',
        timeout=7,
        num_digits=1,
        retries=0, # Manual handling
        redirect=True
    )
    
    if language == "english":
        get_digits.add(Speak("Menu Level Two. Press 1 to play a message. Press 2 to talk to an associate."))
    else:
        get_digits.add(Speak("Menú Nivel Dos. Presione 1 para escuchar un mensaje. Presione 2 para hablar con un asociado.", language="es-US"))
        
    resp.add(get_digits)
    
    xml_str = resp.to_string()
    print(f"DEBUG XML Level 2 ({language}, retry={retry}):\n{xml_str}")
    
    return app.response_class(xml_str, mimetype='application/xml')

# --- IVR ACTION HANDLER ---
@app.route('/ivr/action_handler', methods=['POST'])
def ivr_action_handler():
    """
    Handles input from Level 2 and executes action.
    """
    digit = request.form.get('Digits')
    language = request.args.get('lang', 'english')
    retry = int(request.args.get('retry', 0))
    
    print(f"DEBUG: Action Input: '{digit}' (Lang: {language}, Retry: {retry})")
    
    resp = Response()
    
    # Case 1: Valid Input
    if digit == '1':
        # Action: Play Audio
        audio_url = f"{NGROK_URL}/public/audio/{language}.mp3"
        print(f"DEBUG: Playing audio from {audio_url}")
        resp.add(Play(audio_url))
        resp.add(Speak("Thank you for listening. Goodbye."))
        return app.response_class(resp.to_string(), mimetype='application/xml')
        
    elif digit == '2':
        # Action: Forward to Associate
        resp.add(Speak("Connecting you to an associate now."))
        dial = Dial()
        dial.add(Number(ASSOCIATE_NUMBER))
        resp.add(dial)
        return app.response_class(resp.to_string(), mimetype='application/xml')

    # Error Handling Logic
    if not digit:
        # Case 2: No Input (Timeout)
        if language == "english":
            message = "Nothing selected."
        else:
            message = "Nada seleccionado." # Simple Translation
    else:
        # Case 3: Invalid Input
        if language == "english":
            message = "Invalid selection."
        else:
            message = "Selección inválida."

    if retry < 1:
        # First Failure: Warn and Retry
        if language == "english":
             resp.add(Speak(f"{message} Please try again."))
        else:
             resp.add(Speak(f"{message} Por favor intente de nuevo.", language="es-US"))
             
        # Re-render Level 2 Menu with retry=1
        # Since ivr_level2_menu is a function returning a response object, 
        # we can't just Redirect to a definition.
        # But we can Redirect to a new route that calls it, OR just render it here.
        # Using Redirect is cleaner for flow flow control, but requires a route.
        # Let's just create a quick Redirect to a helper route or just recurse via Redirect element?
        # Actually, ivr_level2_menu isn't a route, it's a helper.
        # We need a route 'ivr_level2' to redirect to?
        # Simpler: We are in 'action_handler'. We cannot "Call" a function to generate XML for the user's *next* step unless we output that XML now.
        # YES, we can just output the Menu XML directly here!
        
        # HOWEVER, the User pattern suggests Redirect is better to keep URL state clean.
        # Let's make a route for Level 2 Menu Display to allow redirection:
        resp.add(Redirect(f"{NGROK_URL}/ivr/level2_show?lang={language}&retry=1"))
        
    else:
        # Second Failure
        if language == "english":
            resp.add(Speak("No response. Goodbye."))
        else:
            resp.add(Speak("Sin respuesta. Adiós.", language="es-US"))
    
    xml_str = resp.to_string()
    return app.response_class(xml_str, mimetype='application/xml')

# Helper Route to display Level 2 (allows Redirect logic)
@app.route('/ivr/level2_show', methods=['GET', 'POST'])
def ivr_level2_show():
    language = request.args.get('lang', 'english')
    retry = int(request.args.get('retry', 0))
    return ivr_level2_menu(language, retry)

def ivr_level2_retry(language): 
    # Deprecated by new logic, removing
    pass


# --- Serve Static Audio ---
@app.route('/public/audio/<filename>')
def serve_audio(filename):
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
