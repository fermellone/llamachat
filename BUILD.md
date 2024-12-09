# Building LlamaChat for macOS

## Prerequisites

1. **Python 3.13+:**

   ```bash
   brew install python@3.13
   ```

2. **Apple Developer Account** (for code signing and notarization)

## Build Steps

1. **Clone and Setup:**

   ```bash
   git clone <repository_url>
   cd llamachat
   ```

2. **Create Virtual Environment:**

   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -e .
   ```

4. **Configure Environment:**
   Create a `.env` file in the project root:

   ```
   LLAMA_MODEL=llama3.2
   LLAMA_TEMPERATURE=0.7
   LLAMA_MAX_RETRIES=3
   LOG_LEVEL=INFO
   ```

5. **Build the Application:**
   ```bash
   pyinstaller llamachat.spec
   ```
   This creates `LlamaChat.app` in the `dist` directory.

## Creating the DMG

1. **Install create-dmg:**

   ```bash
   brew install create-dmg
   ```

2. **Create DMG:**
   ```bash
   create-dmg \
     --volname "LlamaChat" \
     --volicon "llamachat.icns" \
     --window-pos 200 120 \
     --window-size 600 400 \
     --icon-size 100 \
     --icon "LlamaChat.app" 300 190 \
     --hide-extension "LlamaChat.app" \
     "LlamaChat.dmg" \
     "dist/"
   ```

## Code Signing and Notarization (Optional)

These steps are only required if you plan to distribute the app:

1. **Sign the Application:**

   ```bash
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: Your Name" \
     dist/LlamaChat.app
   ```

2. **Notarize:**

   ```bash
   xcrun notarytool submit LlamaChat.dmg \
     --keychain-profile "AC_PASSWORD" \
     --wait
   ```

3. **Staple:**
   ```bash
   xcrun stapler staple LlamaChat.dmg
   ```

## Verification

Test the signed and notarized application:

```bash
spctl --assess --verbose
```
