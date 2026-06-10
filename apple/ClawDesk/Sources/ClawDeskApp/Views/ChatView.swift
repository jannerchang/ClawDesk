import SwiftUI

public struct ChatView: View {
    public let channel: Channel

    @State private var messages: [Message] = []
    @State private var newMessageText = ""
    @State private var isLoading = false
    @State private var errorMessage: String?
    @State private var infoMessage: String?

    @State private var isSelectionMode = false
    @State private var selectedMessageIds = Set<String>()
    @State private var showCreateSubchannelSheet = false
    @State private var subchannelName = ""
    @State private var isCreatingSubchannel = false

    private let apiClient = APIClient.shared

    public init(channel: Channel) {
        self.channel = channel
    }

    public var body: some View {
        VStack(spacing: 0) {
            if isSelectionMode {
                selectionBar
            }

            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(messages) { message in
                            HStack {
                                if isSelectionMode {
                                    selectionToggle(for: message)
                                }

                                MessageBubble(message: message, isCurrentUser: message.isUserMessage)
                            }
                            .id(message.id)
                        }
                    }
                    .padding(.vertical)
                }
                .onChange(of: messages) { _, newMessages in
                    if let lastMessage = newMessages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }
            .overlay {
                if isLoading && messages.isEmpty {
                    ProgressView()
                } else if let errorMessage, messages.isEmpty {
                    ContentUnavailableView(
                        "Failed to Load Messages",
                        systemImage: "exclamationmark.triangle",
                        description: Text(errorMessage)
                    )
                }
            }

            if let infoMessage {
                Text(infoMessage)
                    .font(.footnote)
                    .foregroundStyle(.secondary)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .padding(.horizontal)
                    .padding(.vertical, 6)
            }

            Divider()
            inputBar
        }
        .navigationTitle("# \(channel.name)")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .toolbar {
            ToolbarItem(placement: .primaryAction) {
                Button(isSelectionMode ? "Cancel" : "Select") {
                    withAnimation {
                        isSelectionMode.toggle()
                        if !isSelectionMode {
                            selectedMessageIds.removeAll()
                        }
                    }
                }
            }
        }
        .sheet(isPresented: $showCreateSubchannelSheet) {
            createSubchannelSheet
        }
        .task {
            await loadMessages()
        }
        .refreshable {
            await loadMessages()
        }
    }

    private var selectionBar: some View {
        HStack {
            Text("\(selectedMessageIds.count) selected")
                .font(.subheadline)
                .fontWeight(.semibold)
            Spacer()
            Button("Create Subchannel") {
                subchannelName = suggestedSubchannelName()
                showCreateSubchannelSheet = true
            }
            .buttonStyle(.borderedProminent)
            .disabled(selectedMessageIds.isEmpty)
        }
        .padding()
        .background(Color.blue.opacity(0.1))
        .transition(.move(edge: .top).combined(with: .opacity))
    }

    private var inputBar: some View {
        HStack(spacing: 12) {
            TextField("Message #\(channel.name)", text: $newMessageText)
                .textFieldStyle(.roundedBorder)
                .onSubmit {
                    Task { await sendMessage() }
                }

            Button {
                Task { await sendMessage() }
            } label: {
                Image(systemName: "paperplane.fill")
            }
            .disabled(newMessageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
        }
        .padding()
    }

    private var createSubchannelSheet: some View {
        NavigationStack {
            Form {
                Section("New Subchannel") {
                    TextField("Name", text: $subchannelName)
                    Text("\(selectedMessageIds.count) messages will be copied into the new subchannel.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle("Create Subchannel")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") {
                        showCreateSubchannelSheet = false
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task { await createSubchannel() }
                    }
                    .disabled(subchannelName.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isCreatingSubchannel)
                }
            }
        }
    }

    private func selectionToggle(for message: Message) -> some View {
        Button {
            if selectedMessageIds.contains(message.id) {
                selectedMessageIds.remove(message.id)
            } else {
                selectedMessageIds.insert(message.id)
            }
        } label: {
            Image(systemName: selectedMessageIds.contains(message.id) ? "checkmark.circle.fill" : "circle")
                .foregroundColor(.blue)
                .padding(.trailing, 4)
        }
        .buttonStyle(.plain)
    }

    private func loadMessages() async {
        isLoading = true
        errorMessage = nil
        do {
            messages = try await apiClient.fetchMessages(channelId: channel.id)
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func sendMessage() async {
        let content = newMessageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }

        newMessageText = ""
        do {
            let sentMessage = try await apiClient.sendMessage(channelId: channel.id, content: content)
            messages.append(sentMessage)
        } catch {
            infoMessage = "Failed to send message: \(error.localizedDescription)"
        }
    }

    private func createSubchannel() async {
        let name = subchannelName.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !name.isEmpty, !selectedMessageIds.isEmpty else { return }

        isCreatingSubchannel = true
        defer { isCreatingSubchannel = false }

        let orderedSelectedIds = messages.map(\.id).filter { selectedMessageIds.contains($0) }
        do {
            let subchannel = try await apiClient.createSubchannelFromMessages(
                channelId: channel.id,
                name: name,
                type: channel.type,
                sourceMessageIds: orderedSelectedIds
            )
            infoMessage = "Created subchannel: \(subchannel.name)"
            showCreateSubchannelSheet = false
            isSelectionMode = false
            selectedMessageIds.removeAll()
            await loadMessages()
        } catch {
            infoMessage = "Failed to create subchannel: \(error.localizedDescription)"
        }
    }

    private func suggestedSubchannelName() -> String {
        guard let first = messages.first(where: { selectedMessageIds.contains($0.id) }) else {
            return "新子频道"
        }
        let trimmed = first.content.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed.isEmpty { return "新子频道" }
        return String(trimmed.prefix(20))
    }
}
