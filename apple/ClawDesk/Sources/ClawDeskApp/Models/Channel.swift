import Foundation

public struct Channel: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let spaceId: String
    public let parentChannelId: String?
    public let name: String
    public let type: String
    public let mode: String
    public let status: String
    public let description: String?
    public let tags: [String]
    public let agentConfigId: String?
    public let sourceMessageIds: [String]
    public let createdAt: Date
    public let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case spaceId = "space_id"
        case parentChannelId = "parent_channel_id"
        case name
        case type
        case mode
        case status
        case description
        case tags
        case agentConfigId = "agent_config_id"
        case sourceMessageIds = "source_message_ids"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    public init(
        id: String,
        spaceId: String,
        parentChannelId: String? = nil,
        name: String,
        type: String = "normal",
        mode: String = "mixed",
        status: String = "active",
        description: String? = nil,
        tags: [String] = [],
        agentConfigId: String? = nil,
        sourceMessageIds: [String] = [],
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.spaceId = spaceId
        self.parentChannelId = parentChannelId
        self.name = name
        self.type = type
        self.mode = mode
        self.status = status
        self.description = description
        self.tags = tags
        self.agentConfigId = agentConfigId
        self.sourceMessageIds = sourceMessageIds
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }
}

public struct SubchannelFromMessagesRequest: Codable, Sendable {
    public let name: String
    public let type: String
    public let mode: String
    public let status: String
    public let description: String?
    public let tags: [String]
    public let sourceMessageIds: [String]

    enum CodingKeys: String, CodingKey {
        case name
        case type
        case mode
        case status
        case description
        case tags
        case sourceMessageIds = "source_message_ids"
    }

    public init(
        name: String,
        type: String = "normal",
        mode: String = "mixed",
        status: String = "active",
        description: String? = nil,
        tags: [String] = [],
        sourceMessageIds: [String]
    ) {
        self.name = name
        self.type = type
        self.mode = mode
        self.status = status
        self.description = description
        self.tags = tags
        self.sourceMessageIds = sourceMessageIds
    }
}
