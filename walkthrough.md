# FinSense System Walkthrough

## Overview
This walkthrough is intended for demos, onboarding, and validation. FinSense now supports two distinct workflows:

- Capture Conversation for Groq-powered batch analysis.
- Live Streaming for realtime browser microphone sessions using free and open-source components.

## Demo Flow
1. Start the full stack with:
   ```bash
   .\start.bat
   ```
2. Open the Streamlit app in your browser.
3. Use the Capture Conversation tab to upload or record a finished conversation and review the full analysis.
4. Use the Live Streaming tab to start a session, grant microphone access, and observe realtime transcript and KPI updates.
5. Open the Conversation History tab to review persisted sessions and edit transcripts if needed.

## What to Verify
- Batch upload completes successfully when `GROQ_API_KEY` is present.
- Live sessions can start without any paid service credentials.
- Transcript, entities, sentiment, risk, and intent update incrementally during live recording.
- Finalization produces a complete record in MongoDB and the history view.

## Operational Notes
- Keep `GROQ_API_KEY` only for the Capture Conversation flow.
- Use Redis in production if multiple backend workers or instances will share realtime state.
- Prefer Docker Compose for a production-like local environment.
