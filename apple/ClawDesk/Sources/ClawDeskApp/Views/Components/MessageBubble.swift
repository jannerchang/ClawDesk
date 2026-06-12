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
        HStack(alignment: .bottom) {
            if isCurrentUser {
                Spacer(minLength: 80)
            }

            VStack(alignment: isCurrentUser ? .trailing : .leading, spacing: 4) {
                if !isCurrentUser {
                    Text(message.senderName)
                        .font(.caption2)
                        .foregroundColor(.secondary)
                        .padding(.leading, 6)
                }

                VStack(alignment: .leading, spacing: 8) {
                    renderedContent
                        .textSelection(.enabled)
                        .font(.system(size: 14))

                    ForEach(attachments) { attachment in
                        AttachmentCard(attachment: attachment, isCurrentUser: isCurrentUser)
                    }
                }
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(bubbleColor)
                .foregroundColor(isCurrentUser ? .white : .primary)
                .clipShape(RoundedRectangle(cornerRadius: 16, style: .continuous))
                .shadow(color: Color.black.opacity(0.04), radius: 1, y: 1)

                Text(message.createdAt, style: .time)
                    .font(.caption2)
                    .foregroundColor(.secondary)
                    .padding(.horizontal, 6)
            }
            .frame(maxWidth: 560, alignment: isCurrentUser ? .trailing : .leading)

            if !isCurrentUser {
                Spacer(minLength: 80)
            }
        }
        .padding(.horizontal, 18)
        .padding(.vertical, 2)
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
            return Color(red: 0.18, green: 0.54, blue: 0.86)
        }
        if message.senderType == "hermes" {
            return Color(nsColor: .windowBackgroundColor)
        }
        return Color.gray.opacity(0.16)
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
        .background(isCurrentUser ? Color.white.opacity(0.14) : Color.gray.opacity(0.10))
        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
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
