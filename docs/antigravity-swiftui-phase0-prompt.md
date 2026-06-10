You are Antigravity CLI acting as a coding worker for Janner's local project ClawDesk.

Workdir: /Users/janner/Projects/ClawDesk

Task: Create an Apple SwiftUI client skeleton under apple/ClawDesk/ for Phase 0/1.

Product context:
ClawDesk is a private Apple-platform, local-first agent workspace. It uses lightweight chat, spaces, channels/subchannels, local backend, and Hermes replies. The backend will be FastAPI at http://127.0.0.1:8000 with endpoints for spaces, channels, and messages.

Implement a minimal SwiftUI code skeleton only. Avoid requiring Xcode project generation if not feasible from CLI; a Swift Package or source tree is acceptable, but organize it so it can be pasted/imported into an Xcode multiplatform app.

Requirements:
1. Create under apple/ClawDesk/:
   - README.md
   - Sources/ClawDeskApp/ClawDeskApp.swift
   - Sources/ClawDeskApp/Models/Space.swift
   - Sources/ClawDeskApp/Models/Channel.swift
   - Sources/ClawDeskApp/Models/Message.swift
   - Sources/ClawDeskApp/Services/APIClient.swift
   - Sources/ClawDeskApp/Views/SpaceListView.swift
   - Sources/ClawDeskApp/Views/ChannelListView.swift
   - Sources/ClawDeskApp/Views/ChatView.swift
   - Sources/ClawDeskApp/Views/Components/MessageBubble.swift
2. Use SwiftUI and async/await URLSession.
3. Base URL default http://127.0.0.1:8000, configurable in APIClient.
4. SpaceListView loads GET /spaces.
5. ChannelListView loads GET /spaces/{space_id}/channels.
6. ChatView loads GET /channels/{channel_id}/messages and sends POST /channels/{channel_id}/messages with content.
7. Include a placeholder selection mode for future "create subchannel from selected messages" but do not implement API yet.
8. Keep UI simple: NavigationStack -> spaces -> channels -> chat.
9. Include notes for iOS simulator using localhost and physical device needing Mac LAN/Tailscale address.
10. Do not add secrets. Do not make external network calls beyond configurable local backend.

Verification:
- If possible, run swift syntax/type check. If no Package.swift is used, at least run xcrun swiftc -parse on source files where practical or explain blocker.
- Return concise summary of files changed and verification result.
