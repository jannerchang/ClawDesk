# ClawDesk SwiftUI Client Skeleton

A minimal SwiftUI client skeleton for ClawDesk, designed to interface with the local FastAPI backend.

## Structure

```text
apple/ClawDesk/
├── Package.swift
├── README.md
└── Sources/
    └── ClawDeskApp/
        ├── ClawDeskApp.swift
        ├── Models/
        │   ├── Space.swift
        │   ├── Channel.swift
        │   └── Message.swift
        ├── Services/
        │   └── APIClient.swift
        └── Views/
            ├── SpaceListView.swift
            ├── ChannelListView.swift
            ├── ChatView.swift
            └── Components/
                └── MessageBubble.swift
```

## How to Import/Paste into Xcode

1. Open Xcode and create a new **Multiplatform App** (or iOS/macOS app).
2. Drag and drop the `Sources/ClawDeskApp` directory into your Xcode project navigator (ensure "Copy items if needed" is selected, or add them as references).
3. If importing as a Swift Package:
   - In Xcode, select **File** -> **Add Package Dependencies...** -> **Add Local...** and choose the `apple/ClawDesk` folder.
   - Link the `ClawDeskApp` library target to your application.

## Configuration & Local Testing

The client relies on `APIClient` for communications with the local FastAPI backend:

- **Default Endpoint**: `http://127.0.0.1:8000`
- To change the URL, modify the `baseURLString` property inside [APIClient.swift](file:///Users/janner/Projects/ClawDesk/apple/ClawDesk/Sources/ClawDeskApp/Services/APIClient.swift).

### Simulator vs Physical Device Networking

1. **iOS Simulator / macOS Native App**:
   - The default `http://127.0.0.1:8000` (localhost) will work out of the box because the simulator shares the host machine's network stack.
2. **Physical iOS/iPadOS Devices**:
   - `127.0.0.1` refers to the physical device itself, which will fail to reach your Mac.
   - Find your Mac's Local Area Network (LAN) IP (e.g., `http://192.168.x.x:8000`) or your Tailscale IP (e.g., `http://100.x.y.z:8000`).
   - Configure `APIClient.shared.baseURLString` to use this address.
   - Make sure your FastAPI backend is binding to all interfaces (e.g., `uvicorn main:app --host 0.0.0.0 --port 8000`) so it accepts connections from external network interfaces.
   - **Local Network Permission**: When running on a physical device, you must enable **Local Network** privacy permissions or use a Tailscale/VPN profile if applicable.
   - **ATS (App Transport Security)**: If your backend is served over HTTP (non-HTTPS), you must configure your iOS app's `Info.plist` to allow arbitrary loads or add an exception for your specific IP range to prevent iOS from blocking the connection.
