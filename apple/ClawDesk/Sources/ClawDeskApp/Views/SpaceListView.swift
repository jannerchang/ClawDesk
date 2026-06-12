import SwiftUI

public struct SpaceListView: View {
    @State private var spaces: [Space] = []
    @State private var health: HealthResponse?
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var showBackendSettings = false

    private let apiClient = APIClient.shared

    public init() {}

    public var body: some View {
        NavigationStack {
            List {
                Section {
                    backendStatusRow
                }

                Section("Spaces") {
                    ForEach(spaces, id: \.id) { space in
                        NavigationLink(value: space) {
                            HStack(spacing: 10) {
                                Image(systemName: symbolName(for: space.icon))
                                    .foregroundStyle(.blue)
                                    .frame(width: 24)
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(space.name)
                                        .font(.headline)
                                    Text(space.type)
                                        .font(.subheadline)
                                        .foregroundColor(.secondary)
                                }
                            }
                        }
                    }
                }
            }
            .navigationTitle("ClawDesk")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showBackendSettings = true
                    } label: {
                        Image(systemName: "server.rack")
                    }
                    .help("Backend Settings")
                }
            }
            .sheet(isPresented: $showBackendSettings) {
                BackendSettingsView()
            }
            .navigationDestination(for: Space.self) { space in
                ChannelListView(space: space)
            }
            .overlay {
                if isLoading && spaces.isEmpty {
                    ProgressView()
                } else if let errorMessage, spaces.isEmpty {
                    ContentUnavailableView(
                        "Failed to Load Spaces",
                        systemImage: "exclamationmark.triangle",
                        description: Text(errorMessage)
                    )
                } else if spaces.isEmpty {
                    ContentUnavailableView(
                        "No Spaces Found",
                        systemImage: "square.dashed",
                        description: Text("Swipe down to refresh or check backend connection.")
                    )
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

    private var backendStatusRow: some View {
        HStack(spacing: 10) {
            Circle()
                .fill(health?.ok == true ? Color.green : Color.orange)
                .frame(width: 10, height: 10)
            VStack(alignment: .leading, spacing: 2) {
                Text(health?.ok == true ? "Backend Online" : "Backend Not Checked")
                    .font(.subheadline)
                    .fontWeight(.semibold)
                Text("\(apiClient.baseURLString) · Hermes: \(health?.hermesMode ?? "unknown")")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
            Spacer()
            Button {
                Task { await loadSpaces() }
            } label: {
                Image(systemName: "arrow.clockwise")
            }
            .buttonStyle(.borderless)
        }
    }

    private func loadSpaces() async {
        isLoading = true
        errorMessage = nil
        do {
            async let healthTask = apiClient.checkHealth()
            async let spacesTask = apiClient.fetchSpaces()
            health = try await healthTask
            spaces = try await spacesTask
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func symbolName(for icon: String?) -> String {
        switch icon {
        case "tray": return "tray"
        case "wrench": return "wrench.and.screwdriver"
        case "scale": return "scalemass"
        case "books": return "books.vertical"
        case "archivebox", "archive": return "archivebox"
        default: return "bubble.left.and.bubble.right"
        }
    }
}
