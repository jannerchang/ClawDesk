import SwiftUI

public struct ChannelListView: View {
    public let space: Space
    @State private var channels: [Channel] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    private let apiClient = APIClient.shared
    
    public init(space: Space) {
        self.space = space
    }
    
    public var body: some View {
        List(channels, id: \.id) { channel in
            NavigationLink(value: channel) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("# \(channel.name)")
                        .font(.headline)
                    if let desc = channel.description {
                        Text(desc)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
            }
        }
        .navigationTitle(space.name)
        .navigationDestination(for: Channel.self) { channel in
            ChatView(channel: channel)
        }
        .overlay {
            if isLoading {
                ProgressView()
            } else if let errorMessage {
                ContentUnavailableView("Failed to Load Channels", 
                                       systemImage: "exclamationmark.triangle", 
                                       description: Text(errorMessage))
            } else if channels.isEmpty {
                ContentUnavailableView("No Channels", 
                                       systemImage: "number", 
                                       description: Text("There are no channels in this space yet."))
            }
        }
        .refreshable {
            await loadChannels()
        }
        .task {
            await loadChannels()
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
}
