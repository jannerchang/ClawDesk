import SwiftUI

public struct ChannelListView: View {
    public let space: Space
    @State private var channels: [Channel] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showCreateChannelSheet = false
    @State private var newChannelName = ""
    @State private var isCreatingChannel = false

    private let apiClient = APIClient.shared

    public init(space: Space) {
        self.space = space
    }

    public var body: some View {
        List(channels, id: \.id) { channel in
            NavigationLink(value: channel) {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("# \(channel.name)")
                            .font(.headline)
                        if channel.parentChannelId != nil {
                            Text("sub")
                                .font(.caption2)
                                .padding(.horizontal, 6)
                                .padding(.vertical, 2)
                                .background(Color.gray.opacity(0.15))
                                .clipShape(Capsule())
                        }
                    }
                    if let desc = channel.description, !desc.isEmpty {
                        Text(desc)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                            .lineLimit(2)
                    }
                }
            }
        }
        .navigationTitle(space.name)
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button {
                    newChannelName = ""
                    showCreateChannelSheet = true
                } label: {
                    Image(systemName: "plus")
                }
                .help("New Channel")
            }
        }
        .navigationDestination(for: Channel.self) { channel in
            ChatView(channel: channel)
        }
        .sheet(isPresented: $showCreateChannelSheet) {
            createChannelSheet
        }
        .overlay {
            if isLoading && channels.isEmpty {
                ProgressView()
            } else if let errorMessage, channels.isEmpty {
                ContentUnavailableView(
                    "Failed to Load Channels",
                    systemImage: "exclamationmark.triangle",
                    description: Text(errorMessage)
                )
            } else if channels.isEmpty {
                ContentUnavailableView(
                    "No Channels",
                    systemImage: "number",
                    description: Text("Create a channel to start chatting with Hermes.")
                )
            }
        }
        .refreshable {
            await loadChannels()
        }
        .task {
            await loadChannels()
        }
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
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
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

    private func loadChannels() async {
        isLoading = true
        errorMessage = nil
        do {
            channels = try await apiClient.fetchChannels(spaceId: space.id)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func createChannel() async {
        let name = newChannelName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty else { return }

        isCreatingChannel = true
        defer { isCreatingChannel = false }
        do {
            let channel = try await apiClient.createChannel(spaceId: space.id, name: name, type: space.type, mode: "mixed")
            channels.append(channel)
            showCreateChannelSheet = false
            newChannelName = ""
        } catch {
            errorMessage = error.localizedDescription
        }
    }
}
