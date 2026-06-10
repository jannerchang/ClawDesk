import SwiftUI

public struct MessageBubble: View {
    public let message: Message
    public let isCurrentUser: Bool
    
    public init(message: Message, isCurrentUser: Bool) {
        self.message = message
        self.isCurrentUser = isCurrentUser
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
                
                Text(message.content)
                    .padding(.horizontal, 12)
                    .padding(.vertical, 8)
                    .background(isCurrentUser ? Color.blue : Color.gray.opacity(0.2))
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
}

struct MessageBubble_Previews: PreviewProvider {
    static var previews: some View {
        VStack {
            MessageBubble(message: Message(id: "1", channelId: "c1", senderName: "Alice", content: "Hello there!"), isCurrentUser: false)
            MessageBubble(message: Message(id: "2", channelId: "c1", senderName: "Janner", content: "Hi Alice!"), isCurrentUser: true)
        }
    }
}
