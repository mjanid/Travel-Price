import Foundation

struct PriceWatch: Codable, Identifiable {
    let id: String
    let userId: String
    let tripId: String
    let provider: String
    let targetPrice: Int
    let currency: String
    let isActive: Bool
    let alertCooldownHours: Int
    let createdAt: String
    let updatedAt: String
}

// MARK: - Request Models

struct WatchCreateRequest: Encodable {
    let tripId: String
    var provider: String = "google_flights"
    let targetPrice: Int
    var currency: String = "USD"
    var alertCooldownHours: Int = 6
}

struct WatchUpdateRequest: Encodable {
    var targetPrice: Int?
    var isActive: Bool?
    var alertCooldownHours: Int?
}
