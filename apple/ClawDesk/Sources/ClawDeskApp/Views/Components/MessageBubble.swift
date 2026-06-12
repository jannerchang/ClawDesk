import SwiftUI

public struct MessageBubble: View {
    public let message: Message
    public let isCurrentUser: Bool
    public let attachments: [Attachment]

    public init(message: Message, isCurrentUser: Bool, attachments: [Attachment] = []) {
        self.message = message
        self.isCurrentUser = isCurrentUser
        self.attachments = attachments
    }

    public var body: some View {
        HStack {
            if isCurrentUser {
                Spacer()
            }

            VStack(alignment: isCurrentUser ? .trailing : .leading, spacing: 4) {
                Text(message.senderName)
                    .font(.caption2)
                    .foregroundColor(.secondary)

                VStack(alignment: .leading, spacing: 8) {
                    renderedContent
                        .textSelection(.enabled)

                    ForEach(attachments) { attachment in
                        AttachmentCard(attachment: attachment, isCurrentUser: isCurrentUser)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(bubbleColor)
                .foregroundColor(isCurrentUser ? .white : .primary)
                .cornerRadius(12)

                Text(message.createdAt, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
            }

            if !isCurrentUser {
                Spacer()
            }
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
    }

    private var renderedContent: Text {
        do {
            let attributed = try AttributedString(markdown: message.content)
            return Text(attributed)
        } catch {
            return Text(message.content)
        }
    }

    private var bubbleColor: Color {
        if isCurrentUser {
            return .blue
        }
        if message.senderType == "hermes" {
            return Color.purple.opacity(0.16)
        }
        return Color.gray.opacity(0.2)
    }
}

private struct AttachmentCard: View {
    let attachment: Attachment
    let isCurrentUser: Bool

    var body: some View {
        HStack(spacing: 8) {
            Image(systemName: iconName)
                .font(.title3)
            VStack(alignment: .leading, spacing: 2) {
                Text(attachment.originalName)
                    .font(.caption)
                    .fontWeight(.semibold)
                    .lineLimit(1)
                Text("\(attachment.kind) · \(formattedSize)")
                    .font(.caption2)
                    .foregroundStyle(isCurrentUser ? .white.opacity(0.8) : .secondary)
            }
        }
        .padding(8)
        .background(isCurrentUser ? Color.white.opacity(0.14) : Color.white.opacity(0.55))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var iconName: String {
        if attachment.kind == "image" {
            return "photo"
        }
        if attachment.kind == "audio" {
            return "waveform"
        }
        return "doc"
    }

    private var formattedSize: String {
        ByteCountFormatter.string(fromByteCount: Int64(attachment.size), countStyle: .file)
    }
}

struct MessageBubble_Previews: PreviewProvider {
    static var previews: some View {
        VStack {
            MessageBubble(message: Message(id: "1", channelId: "c1", senderName: "Hermes", content: "Hello **there**!"), isCurrentUser: false)
            MessageBubble(
                message: Message(id: "2", channelId: "c1", senderName: "Janner", content: "Hi Hermes!"),
                isCurrentUser: true,
                attachments: [Attachment(id: "a1", messageId: "2", kind: "file", originalName: "note.txt", localPath: "/tmp/note.txt", mimeType: "text/plain", size: 1024, createdAt: Date())]
            )
        }
    }
}
