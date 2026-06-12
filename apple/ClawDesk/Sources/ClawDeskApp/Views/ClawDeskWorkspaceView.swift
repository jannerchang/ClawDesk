import SwiftUI

public struct ClawDeskWorkspaceView: View {
    @State private var spaces: [Space] = []
    @State private var channels: [Channel] = []
    @State private var channelsBySpaceId: [String: [Channel]] = [:]
    @State private var selectedSpace: Space?
    @State private var selectedChannel: Channel?
    @State private var health: HealthResponse?
    @State private var isLoadingSpaces = false
    @State private var isLoadingChannels = false
    @State private var errorMessage: String?
    @State private var showBackendSettings = false
    @State private var showCreateChannelSheet = false
    @State private var newChannelName = ""
    @State private var isCreatingChannel = false

    private let apiClient = APIClient.shared
    private let telegramBlue = Color(red: 0.18, green: 0.54, blue: 0.86)

    public init() {}

    public var body: some View {
        HStack(spacing: 0) {
            folderRail
                .frame(width: 76)
                .background(Color(red: 0.13, green: 0.16, blue: 0.19))

            conversationColumn
                .frame(minWidth: 292, idealWidth: 330, maxWidth: 380)
                .background(Color(nsColor: .windowBackgroundColor))

            Divider()

            chatColumn
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .frame(minWidth: 1020, minHeight: 660)
        .sheet(isPresented: $showBackendSettings) {
            BackendSettingsView()
        }
        .sheet(isPresented: $showCreateChannelSheet) {
            createChannelSheet
        }
        .task {
            await loadInitialData()
        }
    }

    private var folderRail: some View {
        VStack(spacing: 8) {
            Text("C")
                .font(.headline)
                .fontWeight(.bold)
                .foregroundStyle(.white)
                .frame(width: 42, height: 42)
                .background(telegramBlue)
                .clipShape(Circle())
                .padding(.top, 14)
                .padding(.bottom, 6)

            ScrollView {
                VStack(spacing: 8) {
                    ForEach(spaces) { space in
                        folderButton(space)
                    }
                }
                .padding(.vertical, 4)
            }
            .scrollIndicators(.hidden)

            Spacer()

            railIcon("arrow.clockwise", help: "Refresh") {
                Task { await loadInitialData() }
            }

            railIcon("server.rack", help: "Backend Settings") {
                showBackendSettings = true
            }
            .padding(.bottom, 14)
        }
    }

    private func folderButton(_ space: Space) -> some View {
        let selected = selectedSpace?.id == space.id
        return Button {
            Task { await selectSpace(space) }
        } label: {
            VStack(spacing: 4) {
                ZStack(alignment: .leading) {
                    if selected {
                        RoundedRectangle(cornerRadius: 2)
                            .fill(Color.white)
                            .frame(width: 3, height: 28)
                            .offset(x: -12)
                    }
                    Image(systemName: symbolName(for: space.icon))
                        .font(.system(size: 18, weight: .semibold))
                        .frame(width: 42, height: 36)
                        .background(selected ? telegramBlue : Color.white.opacity(0.08))
                        .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
                }
                Text(shortName(for: space))
                    .font(.system(size: 10, weight: selected ? .semibold : .regular))
                    .lineLimit(1)
            }
            .foregroundStyle(selected ? .white : Color.white.opacity(0.72))
        }
        .buttonStyle(.plain)
        .help(space.name)
    }

    private func railIcon(_ name: String, help: String, action: @escaping () -> Void) -> some View {
        Button(action: action) {
            Image(systemName: name)
                .font(.system(size: 17, weight: .semibold))
                .foregroundStyle(Color.white.opacity(0.72))
                .frame(width: 42, height: 36)
                .background(Color.white.opacity(0.07))
                .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
        }
        .buttonStyle(.plain)
        .help(help)
    }

    private var conversationColumn: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 10) {
                HStack(spacing: 10) {
                    Text(selectedSpace?.name ?? "Chats")
                        .font(.system(size: 22, weight: .bold))
                        .lineLimit(1)

                    Spacer()

                    Button {
                        newChannelName = ""
                        showCreateChannelSheet = true
                    } label: {
                        Image(systemName: "square.and.pencil")
                            .font(.system(size: 17, weight: .semibold))
                    }
                    .buttonStyle(.plain)
                    .foregroundStyle(telegramBlue)
                    .disabled(selectedSpace == nil)
                    .help("New Channel")
                }

                HStack(spacing: 8) {
                    Image(systemName: health?.ok == true ? "checkmark.circle.fill" : "exclamationmark.circle")
                        .foregroundStyle(health?.ok == true ? .green : .orange)
                    Text(backendStatusText)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .lineLimit(2)
                }
            }
            .padding(.horizontal, 16)
            .padding(.top, 16)
            .padding(.bottom, 12)

            Divider()

            if isLoadingChannels && channels.isEmpty {
                ProgressView()
                    .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else if channels.isEmpty {
                ContentUnavailableView(
                    "No Channels",
                    systemImage: "bubble.left.and.bubble.right",
                    description: Text("Create a channel to start a conversation.")
                )
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    LazyVStack(spacing: 2) {
                        ForEach(channels) { channel in
                            channelRow(channel)
                        }
                    }
                    .padding(.horizontal, 8)
                    .padding(.vertical, 8)
                }
                .scrollIndicators(.automatic)
            }
        }
    }

    private var chatColumn: some View {
        Group {
            if let selectedChannel {
                ChatView(channel: selectedChannel)
                    .id(selectedChannel.id)
            } else {
                ContentUnavailableView(
                    "Select a Conversation",
                    systemImage: "message",
                    description: Text("Choose a channel from the middle column to chat with Hermes.")
                )
            }
        }
    }

    private func channelRow(_ channel: Channel) -> some View {
        let selected = selectedChannel?.id == channel.id
        return Button {
            selectedChannel = channel
        } label: {
            HStack(spacing: 10) {
                Text(channelInitial(channel))
                    .font(.system(size: 15, weight: .bold))
                    .foregroundStyle(.white)
                    .frame(width: 42, height: 42)
                    .background(channel.parentChannelId == nil ? telegramBlue : Color.purple.opacity(0.82))
                    .clipShape(Circle())

                VStack(alignment: .leading, spacing: 4) {
                    HStack(spacing: 6) {
                        Text(channel.name)
                            .font(.system(size: 14, weight: .semibold))
                            .lineLimit(1)
                        if channel.parentChannelId != nil {
                            Text("sub")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                                .padding(.horizontal, 5)
                                .padding(.vertical, 1)
                                .background(Color.gray.opacity(0.16))
                                .clipShape(Capsule())
                        }
                        Spacer()
                    }
                    Text(channel.description?.isEmpty == false ? channel.description! : "Janner · Hermes")
                        .font(.system(size: 12))
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 8)
            .background(selected ? telegramBlue.opacity(0.15) : Color.clear)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
    }

    private var createChannelSheet: some View {
        NavigationStack {
            Form {
                Section("New Channel") {
                    TextField("Channel name", text: $newChannelName)
                    Text("Janner and Hermes will be added automatically.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("New Channel")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { showCreateChannelSheet = false }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task { await createChannel() }
                    }
                    .disabled(newChannelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isCreatingChannel)
                }
            }
        }
    }

    private var backendStatusText: String {
        if let health, health.ok {
            return "Connected · Hermes: \(health.hermesMode ?? "unknown")"
        }
        return "Backend not connected"
    }

    private func loadInitialData() async {
        isLoadingSpaces = true
        errorMessage = nil
        do {
            async let healthTask = apiClient.checkHealth()
            async let spacesTask = apiClient.fetchSpaces()
            health = try await healthTask
            spaces = try await spacesTask
            if selectedSpace == nil {
                selectedSpace = spaces.first
            } else if let current = selectedSpace, !spaces.contains(where: { $0.id == current.id }) {
                selectedSpace = spaces.first
            }
            if let selectedSpace {
                await loadChannels(space: selectedSpace, useCache: true)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoadingSpaces = false
    }

    private func selectSpace(_ space: Space) async {
        selectedSpace = space
        if let cached = channelsBySpaceId[space.id] {
            channels = cached
            selectedChannel = cached.first
        } else {
            channels = []
            selectedChannel = nil
        }
        await loadChannels(space: space, useCache: true)
    }

    private func loadChannels(space: Space, useCache: Bool) async {
        if useCache, let cached = channelsBySpaceId[space.id], !cached.isEmpty {
            channels = cached
            if selectedChannel == nil || !cached.contains(where: { $0.id == selectedChannel?.id }) {
                selectedChannel = cached.first
            }
        }
        isLoadingChannels = channels.isEmpty
        errorMessage = nil
        do {
            let fetched = try await apiClient.fetchChannels(spaceId: space.id)
            channelsBySpaceId[space.id] = fetched
            if selectedSpace?.id == space.id {
                channels = fetched
                if selectedChannel == nil || !fetched.contains(where: { $0.id == selectedChannel?.id }) {
                    selectedChannel = fetched.first
                }
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoadingChannels = false
    }

    private func createChannel() async {
        guard let selectedSpace else { return }
        let name = newChannelName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        isCreatingChannel = true
        defer { isCreatingChannel = false }
        do {
            let channel = try await apiClient.createChannel(spaceId: selectedSpace.id, name: name, type: selectedSpace.type, mode: "mixed")
            channels.append(channel)
            channelsBySpaceId[selectedSpace.id] = channels
            selectedChannel = channel
            showCreateChannelSheet = false
            newChannelName = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    private func shortName(for space: Space) -> String {
        if space.name.contains("/") {
            return space.name.components(separatedBy: "/").first?.trimmingCharacters(in: .whitespaces) ?? space.name
        }
        return String(space.name.prefix(3))
    }

    private func channelInitial(_ channel: Channel) -> String {
        let trimmed = channel.name.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmed.isEmpty ? "#" : String(trimmed.prefix(1))
    }

    private func symbolName(for icon: String?) -> String {
        switch icon {
        case "tray": return "tray"
        case "wrench": return "wrench.and.screwdriver"
        case "scale": return "scalemass"
        case "books": return "books.vertical"
        case "archivebox", "archive": return "archivebox"
        default: return "folder"
        }
    }
}
