import SwiftUI

public struct ClawDeskWorkspaceView: View {
    @State private var spaces: [Space] = []
    @State private var channels: [Channel] = []
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

    public init() {}

    public var body: some View {
        HStack(spacing: 0) {
            folderRail
                .frame(width: 78)
                .background(Color.gray.opacity(0.10))

            Divider()

            conversationColumn
                .frame(minWidth: 260, idealWidth: 320, maxWidth: 380)
                .background(Color.gray.opacity(0.05))

            Divider()

            chatColumn
                .frame(maxWidth: .infinity, maxHeight: .infinity)
        }
        .frame(minWidth: 980, minHeight: 640)
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
        VStack(spacing: 10) {
            Text("Claw")
                .font(.caption)
                .fontWeight(.bold)
                .foregroundStyle(.secondary)
                .padding(.top, 12)

            ScrollView {
                VStack(spacing: 8) {
                    ForEach(spaces) { space in
                        Button {
                            Task { await selectSpace(space) }
                        } label: {
                            VStack(spacing: 4) {
                                Image(systemName: symbolName(for: space.icon))
                                    .font(.title3)
                                    .frame(width: 42, height: 34)
                                    .background(selectedSpace?.id == space.id ? Color.blue.opacity(0.18) : Color.clear)
                                    .clipShape(RoundedRectangle(cornerRadius: 10))
                                Text(shortName(for: space))
                                    .font(.caption2)
                                    .lineLimit(1)
                            }
                            .foregroundStyle(selectedSpace?.id == space.id ? .blue : .primary)
                        }
                        .buttonStyle(.plain)
                        .help(space.name)
                    }
                }
                .padding(.vertical, 4)
            }

            Spacer()

            Button {
                Task { await loadInitialData() }
            } label: {
                Image(systemName: "arrow.clockwise")
                    .frame(width: 42, height: 34)
            }
            .buttonStyle(.plain)
            .help("Refresh")

            Button {
                showBackendSettings = true
            } label: {
                Image(systemName: "server.rack")
                    .frame(width: 42, height: 34)
            }
            .buttonStyle(.plain)
            .help("Backend Settings")
            .padding(.bottom, 12)
        }
    }

    private var conversationColumn: some View {
        VStack(spacing: 0) {
            VStack(alignment: .leading, spacing: 8) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(selectedSpace?.name ?? "Folders")
                            .font(.title3)
                            .fontWeight(.semibold)
                        Text(backendStatusText)
                            .font(.caption)
                            .foregroundStyle(health?.ok == true ? .green : .secondary)
                            .lineLimit(1)
                    }
                    Spacer()
                    Button {
                        newChannelName = ""
                        showCreateChannelSheet = true
                    } label: {
                        Image(systemName: "plus")
                    }
                    .disabled(selectedSpace == nil)
                    .help("New Channel")
                }

                if let errorMessage {
                    Text(errorMessage)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .lineLimit(2)
                }
            }
            .padding(14)

            Divider()

            if isLoadingChannels {
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
                List(channels, id: \.id, selection: Binding(
                    get: { selectedChannel?.id },
                    set: { id in
                        selectedChannel = channels.first(where: { $0.id == id })
                    }
                )) { channel in
                    channelRow(channel)
                        .tag(channel.id)
                }
                .listStyle(.sidebar)
            }
        }
    }

    private var chatColumn: some View {
        Group {
            if let selectedChannel {
                ChatView(channel: selectedChannel)
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
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: channel.parentChannelId == nil ? "number" : "arrow.turn.down.right")
                .foregroundStyle(.secondary)
                .frame(width: 18)
            VStack(alignment: .leading, spacing: 4) {
                HStack {
                    Text(channel.name)
                        .font(.headline)
                        .lineLimit(1)
                    if channel.parentChannelId != nil {
                        Text("sub")
                            .font(.caption2)
                            .padding(.horizontal, 6)
                            .padding(.vertical, 2)
                            .background(Color.gray.opacity(0.15))
                            .clipShape(Capsule())
                    }
                }
                if let description = channel.description, !description.isEmpty {
                    Text(description)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(2)
                }
            }
        }
        .padding(.vertical, 4)
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
                await loadChannels(space: selectedSpace)
            }
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoadingSpaces = false
    }

    private func selectSpace(_ space: Space) async {
        selectedSpace = space
        selectedChannel = nil
        await loadChannels(space: space)
    }

    private func loadChannels(space: Space) async {
        isLoadingChannels = true
        errorMessage = nil
        do {
            let fetched = try await apiClient.fetchChannels(spaceId: space.id)
            channels = fetched
            if selectedChannel == nil || !fetched.contains(where: { $0.id == selectedChannel?.id }) {
                selectedChannel = fetched.first
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
