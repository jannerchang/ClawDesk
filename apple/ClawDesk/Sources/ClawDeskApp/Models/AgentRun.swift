import Foundation

public struct AgentRun: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let channelId: String?
    public let agentConfigId: String?
    public let agent: String
    public let status: String
    public let inputSnapshot: String?
    public let outputText: String?
    public let model: String?
    public let reasoning: String?
    public let startedAt: Date
    public let finishedAt: Date?
    public let error: String?

    enum CodingKeys: String, CodingKey {
        case id
        case channelId = "channel_id"
        case agentConfigId = "agent_config_id"
        case agent
        case status
        case inputSnapshot = "input_snapshot"
        case outputText = "output_text"
        case model
        case reasoning
        case startedAt = "started_at"
        case finishedAt = "finished_at"
        case error
    }
}

public struct HermesInvokeResponse: Codable, Hashable, Sendable {
    public let agentRun: AgentRun
    public let message: Message

    enum CodingKeys: String, CodingKey {
        case agentRun = "agent_run"
        case message
    }
}

public struct HermesInvokeRequest: Codable, Hashable, Sendable {
    public let prompt: String?
    public let maxContextMessages: Int
    public let profile: String
    public let model: String?
    public let reasoning: String?

    enum CodingKeys: String, CodingKey {
        case prompt
        case maxContextMessages = "max_context_messages"
        case profile
        case model
        case reasoning
    }

    public init(
        prompt: String? = nil,
        maxContextMessages: Int = 20,
        profile: String = "default",
        model: String? = nil,
        reasoning: String? = nil
    ) {
        self.prompt = prompt
        self.maxContextMessages = maxContextMessages
        self.profile = profile
        self.model = model
        self.reasoning = reasoning
    }
}
