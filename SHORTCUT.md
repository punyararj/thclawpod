# iOS Shortcut Setup

Create the iOS Shortcut that connects HomePod to ClawPod.

This doc is written so you can rebuild the Shortcut from scratch. For a fully expanded screenshot of every action (including the HTTP JSON body), see `imageShortcutFull.png`.

## Prerequisites

- iPhone or iPad with iOS 16+
- Shortcuts app
- ClawPod server running and reachable

## Current Shortcut (as shown in `imageShortcutFull.png`)

Name: **Activate the Kraken**

High-level behavior:

1. Set the ClawPod server base URL into a variable (`chat_server`).
2. Speak a greeting ("This is Kraken").
3. Repeat (50 times):
   - Ask for text input (prompt: "Go on?")
   - POST `{ text, speaker }` to `chat_server + "/chat"`
   - Extract `reply` from the JSON response
   - Speak the reply

Note: the shortcut uses the server’s `end_conversation` field to stop cleanly. After speaking the `reply`, it extracts `end_conversation` from the JSON response and stops the shortcut when it’s truthy.

## Step-by-step (rebuild instructions)

### 1) Create the shortcut

Open Shortcuts → tap **+** → name it something memorable.

### 2) Set server URL → `chat_server`

- Add a **Text** action:
  - `http://YOUR-SERVER:7001`
- Add **Set Variable**:
  - Name: `chat_server`
  - Value: the Text action

### 3) Greeting

- Add **Speak Text**:
  - Text: `This is the Kraken`
  - Wait Until Finished: on

### 4) Conversation loop

Add **Repeat** → `50 times`.

Inside the repeat:

#### a) Ask for input

- **Ask for Input**
  - Type: Text
  - Prompt: `Go on?`
  - Allow Multiple Lines: on

#### b) Send to server

- **Get Contents of URL**
  - URL: `chat_server` + `/chat`
  - Method: POST
  - Request Body: JSON
    - `text`: Ask for Input
    - `speaker`: `Alexis` (customize this)

#### c) Get response and Speak

- **Get Dictionary Value**
  - Key: `reply`
  - From: Contents of URL
- **Speak Text**
  - Text: Dictionary Value
  - Wait Until Finished: on

#### d) End conversation when the server says so

- **Get Dictionary Value**
  - Key: `end_conversation`
  - From: Contents of URL
- **If** Dictionary Value is true
  - **Stop This Shortcut**

### 5) Enable for Siri

Tap shortcut name → **Add to Siri** → record the phrase you want.

### 6) HomePod setup (Personal Content + voice recognition)

Apple’s naming has shifted over time; on current iOS/HomePod versions the relevant setting is typically called **Personal Content** (and it works together with **Recognize My Voice**).

Apple Support reference:
- https://support.apple.com/guide/homepod/set-up-siri-apd1841a8f81/homepod

Quick path:

1. Home app → **…** → **Home Settings**
2. **People** → your name
3. Enable **Recognize My Voice**
4. **Personal Content** → enable for the HomePod(s) you want

## Shortcut privacy settings

In the shortcut details screen (ⓘ), check **Privacy** settings:

- Enable **Allow Running When Locked**
- Enable **Allow this shortcut to access** for your ClawPod server URL

## Testing

1. Run the shortcut manually on iPhone first.
2. Verify server receives requests and responds.
3. Then test via "Hey Siri, <your shortcut name>" on HomePod.

## Reference screenshot

- Full expanded screenshot: `imageShortcutFull.png`
