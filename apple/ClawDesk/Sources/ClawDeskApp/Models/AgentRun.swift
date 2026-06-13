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

public struct LocalAgentInvokeResponse: Codable, Hashable, Sendable {
    public let agentRun: AgentRun
    public let message: Message
    public let command: [String]
    public let workspace: String

    enum CodingKeys: String, CodingKey {
        case agentRun = "agent_run"
        case message
        case command
        case workspace
    }
}

public struct LocalAgentInvokeRequest: Codable, Hashable, Sendable {
    public let prompt: String
    public let agent: String
    public let workspace: String?
    public let timeoutSeconds: Int

    enum CodingKeys: String, CodingKey {
        case prompt
        case agent
        case workspace
        case timeoutSeconds = "timeout_seconds"
    }

    public init(
        prompt: String,
        agent: String = "shell",
        workspace: String? = nil,
        timeoutSeconds: Int = 120
    ) {
        self.prompt = prompt
        self.agent = agent
        self.workspace = workspace
        self.timeoutSeconds = timeoutSeconds
    }
}
