import SwiftUI

public struct SpaceListView: View {
    @State private var spaces: [Space] = []
    @State private var isLoading = false
    @State private var errorMessage: String?
    
    private let apiClient = APIClient.shared
    
    public init() {}
    
    public var body: some View {
        NavigationStack {
            List(spaces, id: \.id) { space in
                NavigationLink(value: space) {
                    VStack(alignment: .leading, spacing: 4) {
                        Text(space.name)
                            .font(.headline)
                        Text(space.type)
                            .font(.subheadline)
                            .foregroundColor(.secondary)
                    }
                }
            }
            .navigationTitle("Spaces")
            .navigationDestination(for: Space.self) { space in
                ChannelListView(space: space)
            }
            .overlay {
                if isLoading {
                    ProgressView()
                } else if let errorMessage {
                    ContentUnavailableView("Failed to Load Spaces", 
                                           systemImage: "exclamationmark.triangle", 
                                           description: Text(errorMessage))
                } else if spaces.isEmpty {
                    ContentUnavailableView("No Spaces Found", 
                                           systemImage: "square.dashed", 
                                           description: Text("Swipe down to refresh or check backend connection."))
                }
            }
            .refreshable {
                await loadSpaces()
            }
            .task {
                await loadSpaces()
            }
        }
    }
    
    private func loadSpaces() async {
        isLoading = true
        errorMessage = nil
        do {
            spaces = try await apiClient.fetchSpaces()
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }
}
