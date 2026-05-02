# Mr Chow Voice Project (Saved)

Status: **Paused** (resume later)
Last updated: 2026-04-15

## Goal
Build a dedicated “Mr Chow” voice for Chow Telegram bot (not just stock voice), with production-safe implementation.

## Chosen Direction
- Keep STT + reasoning path as-is (Gemini for transcription/chat).
- Add separate TTS provider layer for custom voice ID support.
- Prioritize legally safe “Mr Chow energy” custom voice over exact celebrity clone.

## Current Findings (already validated)
- Existing candidate voices found online (including Leslie Chow/Ken Jeong style entries).
- cvoice dataset has deployable entry:
  - slug: `ken-jeong`
  - `voice_id`: `99f2fa9b-e55a-4889-bb00-02bc590026f8`
- Jammable has discoverable model entries:
  - `leslie-chow-GrgLx`
  - `custom-ken-jeong`

## Resume Checklist
1. Decide lane:
   - Quick external API voice integration, or
   - Fully custom trained “Mr Chow” voice.
2. Add env split in bot:
   - `VOICE_STT_PROVIDER`
   - `VOICE_TTS_PROVIDER`
   - `VOICE_TTS_API_KEY`
   - `VOICE_TTS_VOICE_ID`
3. Implement provider adapter in `src/bot.ts` for TTS.
4. Keep fallback chain: custom TTS -> Gemini TTS.
5. QA in Telegram:
   - `/voice test`
   - real voice-note roundtrip
   - duration/codec checks
6. Optional: add `/voice persona` command for quick switching.

## Notes
- Codec bug (0-second voice notes) was diagnosed and solved by converting PCM/WAV to OGG/Opus before Telegram send.
- Voice tone currently set to deeper masculine fallback (`VOICE_REPLY_VOICE=Charon`).
