import SwiftUI

public struct BackendSettingsView: View {
    @Environment(\.dismiss) private var dismiss
    @State private var baseURLString: String
    @State private var statusText = "Not checked"
    @State private var isChecking = false

    private let apiClient = APIClient.shared

    public init() {
        _baseURLString = State(initialValue: APIClient.shared.baseURLString)
    }

    public var body: some View {
        NavigationStack {
            Form {
                Section("Backend") {
                    TextField("Base URL", text: $baseURLString)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        .autocorrectionDisabled()
                        #endif
                    Text("Examples: http://127.0.0.1:8000 or http://100.x.y.z:8000")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                Section("Connection") {
                    HStack {
                        Text(statusText)
                            .foregroundStyle(statusText == "Connected" ? .green : .secondary)
                        Spacer()
                        if isChecking {
                            ProgressView()
                        }
                    }
                    Button("Save & Check") {
                        Task { await saveAndCheck() }
                    }
                    .disabled(baseURLString.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isChecking)
                }
            }
            .navigationTitle("Backend Settings")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }

    private func saveAndCheck() async {
        let trimmed = baseURLString.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }
        apiClient.baseURLString = trimmed
        isChecking = true
        defer { isChecking = false }
        do {
            statusText = try await apiClient.checkHealth() ? "Connected" : "Backend returned not ok"
        } catch {
            statusText = "Failed: \(error.localizedDescription)"
        }
    }
}
