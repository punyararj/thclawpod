# iOS Shortcut Setup Guide

This guide walks you through creating the iOS Shortcut that bridges HomePod to Clawdpod.

## Prerequisites

- iPhone or iPad with iOS 16+
- Shortcuts app installed
- Clawdpod server running and accessible from your network

## Overview

The Shortcut does this loop:
1. Listen for voice input (Dictate Text)
2. Send transcription to Clawdpod server
3. Speak the response
4. Check if conversation should end
5. If not, go back to step 1

## Step-by-Step Setup

### Step 1: Create New Shortcut

1. Open **Shortcuts** app
2. Tap **+** to create new shortcut
3. Tap the name at top and rename to **"Call Dobby"** (or your assistant's name)

### Step 2: Set Variables

Add these actions at the start:

**Text** action:
- Content: `http://YOUR-SERVER-IP:7001` (your Clawdpod server URL)
- Tap the text, then "Set Variable" → name it `ServerURL`

**Text** action:
- Content: Your name (e.g., `Alexis`) — or use "Get Current User" if available
- Set Variable → name it `Speaker`

### Step 3: Conversation Loop

**Repeat** action (set to repeat many times, e.g., 100):

Inside the repeat block, add:

#### 3a. Get Voice Input

**Dictate Text** action:
- Stop Listening: After Short Pause
- Set the result to variable `UserInput`

#### 3b. Send to Server

**Get Contents of URL** action:
- URL: `ServerURL` variable + `/chat`
  - Tap URL field, insert `ServerURL` variable, then type `/chat`
- Method: POST
- Headers:
  - `Content-Type`: `application/json`
  - (Optional) `Authorization`: `Bearer YOUR-TOKEN` if using auth
- Request Body: JSON
  ```json
  {
    "text": [UserInput variable],
    "speaker": [Speaker variable]
  }
  ```
  - Tap "Add new field" → Text → key: `text` → value: `UserInput` variable
  - Tap "Add new field" → Text → key: `speaker` → value: `Speaker` variable

#### 3c. Parse Response

**Get Dictionary Value** action:
- Get: Value for `reply`
- From: Contents of URL (previous action)
- Set Variable → `Reply`

**Get Dictionary Value** action:
- Get: Value for `end_conversation`
- From: Contents of URL
- Set Variable → `EndConversation`

#### 3d. Speak Response

**Speak Text** action:
- Text: `Reply` variable

#### 3e. Check for End

**If** action:
- Input: `EndConversation`
- Condition: is `true` (or equals 1)

Inside the If:
- **Exit Shortcut** action

(End If)

### Step 4: Enable for Siri

1. Tap the **ⓘ** (info) button at bottom of shortcut
2. Tap **Add to Siri**
3. Record or type: "Call Dobby"
4. Tap **Done**

### Step 5: Test

**On iPhone:**
1. Say "Hey Siri, Call Dobby"
2. When prompted, say something
3. Listen for response
4. Say "goodbye" to end

**On HomePod:**
1. Say "Hey Siri, Call Dobby"
2. The shortcut runs on your iPhone but audio routes to HomePod

## Advanced: Voice Recognition

HomePod can recognize different household members. To pass this to Clawdpod:

### Option A: Manual Speaker Selection

Add a **Choose from Menu** action at the start:
- Options: Alexis, Ringae, Odysseus, Kallisto, Guest
- Set selection to `Speaker` variable

### Option B: Use Current User (if available)

Some Shortcuts contexts provide the current user. Check if "Get Current User" action is available and returns the recognized person.

## Tips

### Smart Apostrophes

iOS uses "smart" curly apostrophes. The phrase "that's all" might become "that's all". Clawdpod handles both, but be aware when debugging.

### Timeout Handling

If the server takes too long, the Shortcut may error. The default 60-second timeout should be sufficient, but you can add error handling:

**Get Contents of URL** → tap ⓧ → "Continue on Error"

Then add an **If** to check if the result is valid.

### Personal Requests

For HomePod to run Shortcuts, you may need to enable "Personal Requests":
1. Open **Home** app
2. Tap your HomePod
3. Scroll to **Personal Requests** → Enable

This routes Shortcut execution to your paired iPhone.

### Testing Without HomePod

Test the Shortcut directly on iPhone first. Tap the play button in Shortcuts to run it locally before trying on HomePod.

## Example Conversation

```
You: "Hey Siri, Call Dobby"
Siri: [activates shortcut, starts listening]
You: "What's on my calendar today?"
Dobby: "You have a dentist appointment at 2pm and dinner with friends at 7."
You: "Remind me to bring the wine"
Dobby: "I've set a reminder for 6:30pm to bring wine for dinner."
You: "Thanks, that's all"
Dobby: "Goodbye! Talk to you later."
[Shortcut ends]
```

## Troubleshooting

**"Sorry, I can't do that"**
- Check HomePod Personal Requests are enabled
- Ensure iPhone is on same network as HomePod

**No response / timeout**
- Verify server is reachable: `curl http://server:7001/health`
- Check server logs for errors

**"The server returned an error"**
- Check Clawdpod logs
- Verify JSON formatting in Shortcut
- Test with curl first

**Shortcut doesn't appear on HomePod**
- Re-add Siri phrase
- Check Shortcut sharing settings

## Screenshots

_TODO: Add annotated screenshots of each step_
