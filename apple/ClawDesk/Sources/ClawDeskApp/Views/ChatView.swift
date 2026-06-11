import SwiftUI
import UniformTypeIdentifiers

public struct ChatView: View {
    public let channel: Channel

    @State private var messages: [Message] = []
    @State private var members: [User] = []
    @State private var newMessageText = ""
    @State private var isLoading = false
    @State private var isSending = false
    @State private var isInvokingHermes = false
    @State private var isUploadingAttachment = false
    @State private var errorMessage: String?
    @State private var infoMessage: String?

    @State private var isSelectionMode = false
    @State private var selectedMessageIds = Set<String>()
    @State private var showCreateSubchannelSheet = false
    @State private var showFileImporter = false
    @State private var subchannelName = ""
    @State private var isCreatingSubchannel = false

    private let apiClient = APIClient.shared

    public init(channel: Channel) {
        self.channel = channel
    }

    public var body: some View {
        VStack(spacing: 0) {
            memberBar

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
                    .foregroundStyle(infoMessage.hasPrefix("Failed") ? .red : .secondary)
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
        .fileImporter(isPresented: $showFileImporter, allowedContentTypes: [.item], allowsMultipleSelection: false) { result in
            handleFileImport(result)
        }
        .task {
            await loadMessages()
        }
        .refreshable {
            await loadMessages()
        }
    }

    private var memberBar: some View {
        HStack(spacing: 8) {
            ForEach(members) { member in
                HStack(spacing: 4) {
                    Text(member.avatar ?? String(member.name.prefix(1)))
                        .font(.caption2)
                        .frame(width: 20, height: 20)
                        .background(member.kind == "bot" ? Color.purple.opacity(0.18) : Color.blue.opacity(0.18))
                        .clipShape(Circle())
                    Text(member.name)
                        .font(.caption)
                    if member.kind == "bot" {
                        Text("bot")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.10))
                .clipShape(Capsule())
            }
            Spacer()
        }
        .padding(.horizontal)
        .padding(.vertical, 6)
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
            Button {
                showFileImporter = true
            } label: {
                if isUploadingAttachment {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Image(systemName: "plus.circle")
                }
            }
            .disabled(isSending || isInvokingHermes || isUploadingAttachment)

            Button {
                Task { await askHermes() }
            } label: {
                if isInvokingHermes {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Label("Ask Hermes", systemImage: "sparkles")
                }
            }
            .disabled(isSending || isInvokingHermes || isUploadingAttachment)

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
            .disabled(newMessageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || isSending || isInvokingHermes || isUploadingAttachment)
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
        async let messagesTask = apiClient.fetchMessages(channelId: channel.id)
        async let membersTask = apiClient.fetchChannelMembers(channelId: channel.id)
        do {
            messages = try await messagesTask
            members = try await membersTask
        } catch {
            errorMessage = error.localizedDescription
        }
        isLoading = false
    }

    private func sendMessage() async {
        let content = newMessageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !content.isEmpty else { return }

        newMessageText = ""
        isSending = true
        defer { isSending = false }

        do {
            let sentMessage = try await apiClient.sendMessage(channelId: channel.id, content: content)
            messages.append(sentMessage)
            infoMessage = nil
        } catch {
            infoMessage = "Failed to send message: \(error.localizedDescription)"
        }
    }

    private func askHermes() async {
        guard !isInvokingHermes else { return }

        isInvokingHermes = true
        infoMessage = nil
        defer { isInvokingHermes = false }

        do {
            let response = try await apiClient.invokeHermes(channelId: channel.id, prompt: nil)
            upsertMessage(response.message)
        } catch {
            infoMessage = "Failed to ask Hermes: \(error.localizedDescription)"
        }
    }

    private func upsertMessage(_ message: Message) {
        if let index = messages.firstIndex(where: { $0.id == message.id }) {
            messages[index] = message
        } else {
            messages.append(message)
        }
    }

    private func handleFileImport(_ result: Result<[URL], Error>) {
        switch result {
        case .success(let urls):
            guard let fileURL = urls.first else { return }
            Task { await uploadAttachment(fileURL: fileURL) }
        case .failure(let error):
            infoMessage = "Failed to choose file: \(error.localizedDescription)"
        }
    }

    private func uploadAttachment(fileURL: URL) async {
        guard !isUploadingAttachment else { return }
        isUploadingAttachment = true
        infoMessage = nil
        defer { isUploadingAttachment = false }

        let didAccess = fileURL.startAccessingSecurityScopedResource()
        defer {
            if didAccess {
                fileURL.stopAccessingSecurityScopedResource()
            }
        }

        do {
            let fileName = fileURL.lastPathComponent.isEmpty ? "attachment" : fileURL.lastPathComponent
            let placeholder = try await apiClient.sendMessage(
                channelId: channel.id,
                content: "📎 \(fileName)",
                senderName: "Janner"
            )
            upsertMessage(placeholder)
            let attachment = try await apiClient.uploadAttachment(messageId: placeholder.id, fileURL: fileURL)
            infoMessage = "Uploaded attachment: \(attachment.originalName)"
        } catch {
            infoMessage = "Failed to upload attachment: \(error.localizedDescription)"
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
