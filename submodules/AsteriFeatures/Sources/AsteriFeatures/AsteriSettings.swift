import Foundation

/// Local presentation preferences. Never changes message storage or transport.
public struct AsteriSettings: Codable, Equatable {
    public var filterZalgo: Bool

    public static var defaultSettings: AsteriSettings {
        return AsteriSettings(filterZalgo: true)
    }

    public init(filterZalgo: Bool) {
        self.filterZalgo = filterZalgo
    }

    private enum CodingKeys: String, CodingKey {
        case filterZalgo
    }

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        self.filterZalgo = try container.decodeIfPresent(Bool.self, forKey: .filterZalgo) ?? true
    }
}
