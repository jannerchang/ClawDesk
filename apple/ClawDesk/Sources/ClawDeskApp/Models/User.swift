import Foundation

public struct User: Codable, Identifiable, Hashable, Sendable {
    public let id: String
    public let name: String
    public let kind: String
    public let avatar: String?
    public let description: String?
    public let role: String?
    public let createdAt: Date
    public let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case kind
        case avatar
        case description
        case role
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}
