📞 InspireWorks – Plivo Voice API IVR Demo

**Master Build Instructions**

---

## 1. Objective

Build a **working demo IVR system** that demonstrates  **Plivo Voice API capabilities** , including:

* Outbound call initiation
* Multi-level IVR menus
* DTMF input handling
* Branching call logic
* Audio playback
* Call forwarding to a live associate

This project is for  **demonstration and interview evaluation** , not production scale.

---

## 2. Functional Requirements

### 2.1 Outbound Call

* Implement a backend endpoint or script that:
  * Initiates an outbound call using **Plivo Voice API**
  * Accepts a **target phone number** via:
    * API request (preferred), or
    * Configuration variable
* Use Plivo’s `calls.create()` API
* Configure a webhook (`answer_url`) to receive call control instructions

---

### 2.2 IVR Menu Structure

#### Level 1 – Language Selection

Prompt the callee with:

* Press **1** → English
* Press **2** → Spanish

Requirements:

* Use **DTMF input**
* Timeout handling
* Retry invalid inputs
* Graceful fallback if no input is received

---

#### Level 2 – Action Menu (Language-Specific)

After language selection, present:

* Press **1** → Play an audio message
* Press **2** → Connect to a live associate (placeholder number)

Requirements:

* Different prompts for English and Spanish
* Correct branching based on user input
* Audio must be:
  * Publicly hosted
  * Played using Plivo `<Play>` or equivalent
* Call forwarding must use Plivo `<Dial>`

---

### 2.3 Multi-Level Flow Handling

* Correctly capture DTMF input at each level
* Maintain clean call flow transitions
* Handle:
  * Invalid input
  * No input
  * Retry limits
* Ensure the caller is never stuck in a dead end

---

## 3. Technical Requirements

### 3.1 Backend

* Language: **Python**
* Framework: **Flask** (preferred)
* Must expose:
  * Endpoint to trigger outbound calls
  * Webhook endpoints for IVR logic
* Use **Plivo XML (plivoxml)** for call control

---

### 3.2 Plivo Integration

* Use environment variables for:
  * `PLIVO_AUTH_ID`
  * `PLIVO_AUTH_TOKEN`
* Do NOT hardcode credentials
* Use:
  * `GetDigits`
  * `Speak`
  * `Play`
  * `Dial`
  * `Redirect`

---

### 3.3 IVR Logic Rules

* Level 1 → Language selection
* Level 2 → Action selection
* Each menu must:
  * Define timeout
  * Define retry count
  * Redirect on invalid input
* Ensure call flow loops cleanly when needed

---

## 4. Optional (Bonus)

These are  **not mandatory** , but allowed:

* Simple HTML page or CLI command to trigger outbound calls
* Dockerfile for local setup
* Logging of call UUIDs
* Configurable associate number

---

## 5. Deliverables

### 5.1 Working Application

* Backend server that:
  * Initiates outbound calls
  * Serves IVR logic via webhooks
* Fully functional IVR navigation:
  * Level 1 → Level 2
  * Audio playback
  * Call forwarding

---

### 5.2 Code Repository Structure

Expected structure:

```
project-root/
│
├── app.py
├── requirements.txt
├── README.md
└── audio/
    ├── english.mp3
    └── spanish.mp3
```

---

### 5.3 README.md Must Include

* Project overview
* Setup instructions
* Required environment variables
* Steps to run locally
* How to test the IVR
* Example curl command to trigger call

---

### 5.4 Demo Video (3–5 minutes)

Show:

* Outbound call being triggered
* Language selection
* Level 2 navigation
* Audio playback
* Call forwarding
* Invalid input handling

---

## 6. Code Quality Expectations

* Clean, readable code
* Clear function separation
* No hardcoded secrets
* Simple logic (no over-engineering)
* Comment important IVR decisions

---

## 7. Constraints & Assumptions

* This is a  **demo** , not production
* Use placeholder phone numbers where needed
* Public audio files may be dummy content
* Assume webhook exposure via **ngrok**

---

## 8. Output Expectations From AI

When generating the solution, the AI must:

* Produce **fully working code**
* Include **complete Flask + Plivo XML logic**
* Provide **exact commands to run**
* Avoid pseudo-code
* Avoid vague placeholders like “handle logic here”

---

## 9. Success Criteria

The solution is successful if:

* An outbound call is placed
* Caller navigates both IVR levels
* Audio plays correctly
* Call forwarding works
* Invalid input is handled gracefully

---

## 10. Final Instruction

> **Generate the complete implementation exactly as specified above, with no missing components.**
