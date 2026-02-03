# ClawPod

Talk to OpenClaw through Apple HomePod.

ClawPod bridges HomePod’s voice interface to [OpenClaw](https://openclaw.ai/), letting you have conversations with your AI assistant through any HomePod in your home.

## How It Works

It's got two parts, the ClawPod iOS Shortcut and a ClawPod server.

The HomePod acts as a proxy for the ClawPod iOS Shortcut which runs on your iPhone (via Apple Personal Content). That Shortcut connects via HTTP to the ClawPod server, which in turn is a a voice proxy server for the OpenClaw gateway, to which it connects via the `openclaw` command-line client.


```
You: "Hey Siri, Call Dobby"
    ↓
iOS Shortcut activates, listens
    ↓
Speech-to-text via Siri
    ↓
POST /chat → ClawPod server
    ↓
openclaw agent (CLI)
    ↓
Response returned
    ↓
Text-to-speech via Siri
    ↓
HomePod speaks the reply
```

To set it up, you need:

- Apple HomePod (any model)
- iPhone/iPad for creating and running the Shortcut
- Server running OpenClaw (Gateway + CLI available as `openclaw`),
  where you can also install Python and run the ClawPod server.
- Network connectivity between your iOS device and the server

### Setting up the ClawPod Server

The ClawPod server is a single Python script. Use environment variables to configure the address and port where it's serving. You can use `CLAWPOD_AGENT` to control which OpenClaw agent chats are associated with.

```bash
# from your OpenClaw box (or any machine which can run `openclaw agent` and reach the gateway)
cd ~/gits/clawpod

# run the server (uv resolves deps from the inline script metadata)
uv run clawpod_server.py

# sanity check
curl http://localhost:7001/health
```

You can configure it with the usual environment variables:

| Variable                 | Default   | Description                |
|--------------------------|-----------|----------------------------|
| `CLAWPOD_HOST`           | `0.0.0.0` | Bind address               |
| `CLAWPOD_PORT`           | `7001`    | Listen port                |
| `CLAWPOD_LOG_LEVEL`      | `INFO`    | Logging level              |
| `CLAWPOD_API_TOKEN`      | (none)    | Optional bearer token      |
| `CLAWPOD_AGENT`          | `main`    | OpenClaw agent id to use   |
| `CLAWPOD_TIMEOUT`        | `60`      | Response timeout (seconds) |
| `CLAWPOD_SESSION_PREFIX` | `homepod` | Session ID prefix          |

If you want this server always running, then you'll need to setup a systemd or launchctl service definition. Have a look at the ancestral Homechat repo for an example.

And be careful out there. Please don't stick this on the public internet unless you know what you are doing, how to use the binding address and the api token to secure it, etc..

#### Testing the connection to OpenClaw

You can test the connection to OpenClaw with the test script for interactive command line chat, `test_client.py`. Here’s an example from me using it to test the proxy server:

```text
algal@box:~/gits/clawpod$ ./test_client.py
Installed 6 packages in 8ms
🦞 Clawpod Test Client
   Server: http://localhost:7001
   Speaker: Test
   Say 'quit' or 'goodbye' to exit

You: Can you hear me? I'm testing the clawpod server
Dobby: Yes, I can hear you!

The message came through clearly via HomePod. ClawPod server connection is working - your voice transcription looks good!

You: I mean, I'm actually just running test_client.py. No voice yet...
Dobby: Ha, right! You're running `test_client.py` to test the client-server connection, not actual voice input yet. Good way to verify the pipeline is working before adding the real speech-to-text layer.

The connection is solid - when you're ready to try real voice through the HomePod, the plumbing should be all set!

You: Goodbye
Dobby: Goodbye!

[Conversation ended]
```


### Setting up the iOS Shortcut

Once `clawpod` is interacting correctly with your OpenClaw agent, then the next step is to configure your HomePod and your iOS device to interact with the server.

For that, you need the ClawPod iOS Shortcut. In the repo, I’ve included a copy of the iOS Shortcut I use, which you can install on your system and then adjust as needed.

Here’s what the Shortcut's action sequence looks like:

<Image src={shortcutDefinitionImg} alt="Screenshot of the ClawPod iOS Shortcut definition" />

In particular, you will want to modify these parts of the Shortcut:

1. **ClawPod URL.** The URL which describes how to reach the ClawPod server within your subnet.
  
   For me, this is `https://box.local:7001`. For you, it’s presumably something else.

2. **Name** The name of the Shortcut.

   The name of the Shortcut defines which phrase you will use to ask Siri in order to invoke the Shortcut. The screen shot calls it "Activate the Kraken" but lately I've settled on "Lobster Time". Have fun with it! Also, find a name which fits your agent's persona, and which is not easily confused by Siri with contacts, music items, or other entities on your phone.
   
3. **Speaker**. Your name. If every user configures their shortcut with their personal name, then Siri will recognize the speaker, run the right person's Shortcut, and the agent will know who is talking.

Additional Shortcut customization notes are in the footnote.[^shortcut-notes]

Once you’ve added this Shortcut to your iOS device, there’s a third step: you need to configure your iOS device and your HomePod so that the HomePod will be able to invoke this Shortcut.

### Enabling Personal Content (and voice recognition)

Apple’s UI/terminology has shifted over time; on current iOS/HomePod versions, the setting you’re usually looking for is **Personal Content** (along with **Recognize My Voice**).

Apple documents the current flow here:

- [Set up Siri and invite others to use HomePod (Apple Support)](https://support.apple.com/guide/homepod/set-up-siri-apd1841a8f81/homepod)
- [Set up voice recognition on HomePod or HomePod mini (Apple Support)](https://support.apple.com/en-us/108397)

To summarize:

1. On your iPhone/iPad, open the **Home** app.
2. Tap **…** → **Home Settings**.
3. Under **People**, tap **your name**.
4. Turn on **Recognize My Voice**.
5. Tap **Personal Content**, then enable **Personal Content** for the HomePod(s) you want.

Below are screenshots of where these settings live in the Home app:

<div style="display:grid; grid-template-columns: 1fr 1fr; gap: 1rem; align-items: start; max-width: 720px; margin: 0 auto;">
  <div style="max-width: 340px; justify-self: center;">
    <Image src={homePodSettingsImg} alt="Home app: HomePod device settings showing Personal Content / related toggles" />
  </div>
  <div style="max-width: 340px; justify-self: center;">
    <Image src={homeSettingsImg} alt="Home app: Home Settings → People → Personal Content / Recognize My Voice" />
  </div>
</div>

Finally, you should be sure that when you configure the iOS Shortcut on your device, it’s configured so that these settings are enabled: “Personal Content” can be activated from HomePod. These are necessary for requests to make their way all the way to the HomePod.

If Siri doesn’t recognize you (or your voice recognition setup seems flaky), Apple’s troubleshooting checklist is worth a look:

- https://support.apple.com/en-us/108397

[^shortcut-notes]: Other Shortcut details worth customizing / verifying:

    - In **Shortcut → Privacy**:
      - Enable **Allow Running When Locked**.
      - Enable **Allow this shortcut to access** for the URL where your ClawPod server runs (i.e. the host you’re POSTing to).
    - The **Text** note near the beginning of the Shortcut defines the URL of the ClawPod server.
    - The **Speak** action defines the greeting; you’ll likely want to customize it to your agent’s name (just as with the Shortcut name itself).
    - In the **Get Contents of URL** action that POSTs to `/chat`, customize the `speaker` field (the name reported to the server).
    - Full shortcut screenshot (all actions expanded): [imageShortcutFull.png](./assets/imageShortcutFull.png)

### Testing the iOS Shortcut

Once you’ve installed and tested the ClawPod proxy server, and once you’ve installed the iOS Shortcut, you should test that the iOS Shortcut works directly before you expect it to work from the HomePod.

This part is fairly easy. Since iOS Shortcuts are automatically synced via your iCloud account, once you have created this Shortcut, it’s available not only on the HomePod (via iOS), but also on iOS directly, and also on your Mac. The Mac is the easiest way to test, using the Shortcuts app.

### Using it

So you can test it as follows:

If HomePod won’t run the shortcut reliably, try the same phrase on iPhone first (locked-screen Siri) to confirm Siri can resolve the shortcut name. If it works on iPhone but not on HomePod, the problem is usually HomePod voice routing/recognition rather than your ClawPod server.

- Open the Shortcuts app on your Mac. You will see there the Shortcut you have created. (In my case, it’s called “Invoke the Kraken.”)
- If you run the Shortcut, you will be presented with a small text entry modal asking for your first message to send to your agent.
- Type your message.
- Submit.
- After a pause, if all is working well, you should hear it spoken aloud (or else see it printed back out to you).
- You can continue the conversation as usual, and when you’re done, say “goodbye.”

You say “goodbye”; that on its own does not end the conversation. That passes the message to the AI agent, which alone has the power to end the conversation—when it recognizes that word and replies with an end-of-conversation sentinel message.

When you invoke the iOS Shortcut on macOS, you are given this text interface because on macOS you have a keyboard and a screen. But if that worked, then you should be able to invoke the same Shortcut from iOS and from the HomePod.

If you invoke from iOS by running the Shortcut manually when the device is unlocked, you will get the same text entry interface. However, if you invoke the Shortcut from iOS when the device is locked, purely by using Siri’s speech interface, then you will have the full speech-to-speech interaction with your agent.

Once that is working, you can now invoke the same flow by launching the Shortcut from your HomePod. Just say “Hey Siri, invoke the Kraken,” and after a pause, you should get a reply from your agent.

Congratulations. You are now using some of oldest voice asssistant technology (Siri on the HomePod) with the most advanced AI, and the most delightfully whacky assistant technology, of the day.


