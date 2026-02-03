# iOS Shortcut Setup

Create the iOS Shortcut that connects HomePod to ClawPod.

The easiest thing is to import my Shortcut and adjust it. It does the following:

1. Set the ClawPod server base URL into a variable (`chat_server`).
2. Speak a greeting ("This is Kraken").
3. Repeat (50 times):
   - Ask for text input (prompt: "Go on?")
   - POST `{ text, speaker }` to `chat_server + "/chat"`
   - Extract `reply` from the JSON response
   - Speak the reply

Note: the shortcut uses the server’s `end_conversation` field to stop cleanly. After speaking the `reply`, it extracts `end_conversation` from the JSON response and stops the shortcut when it’s truthy.

Here are instructions to build it from scratch. For a fully expanded screenshot of every action (including the HTTP JSON body), see `imageShortcutFull.png`.


## To build the Shortcut from scratch

Here are detailed instructions, for how to make it.

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
    - `speaker`: `Alexis` (customize this so the agent knows who you
      are, by knowing which user's Shortcut is running)

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


### 4) Set Shortcut privacy settings

In the shortcut details screen (ⓘ), check **Privacy** settings:

- Enable **Allow Running When Locked**
- Enable **Allow this shortcut to access** for your ClawPod server URL



### 5) Run it with Siri

Per Apple’s current Shortcuts docs, you can run a shortcut by asking Siri to run it by name.

- Say: **“Hey Siri, <shortcut name>”**

This works from iPhone/iPad, and also from HomePod (assuming your HomePod/iPhone settings allow it).

Apple reference:
- https://support.apple.com/guide/shortcuts/run-shortcuts-with-siri-apd07c25bb38/ios

## To setup your HomePod

To use this you need to enable Personal Content and Recognize my Voice. [Apple docs on Siri on HomePod](https://support.apple.com/guide/homepod/set-up-siri-apd1841a8f81/homepod) keep shifting, but here's where I found the settings:

1. Home app → **…** → **Home Settings**
2. **People** → your name
3. Enable **Recognize My Voice**
4. **Personal Content** → enable for the HomePod(s) you want

