import Foundation

struct PriceAlert: Codable, Identifiable {
    let id: String
    let priceWatchId: String
    let userId: String
    let priceSnapshotId: String
    let alertType: String
    let channel: String
    let status: String
    let targetPrice: Int
    let triggeredPrice: Int
    let message: String?
    let sentAt: String?
    let createdAt: String

    /// How much below target the triggered price was, in cents.
    var savingsCents: Int {
        targetPrice - triggeredPrice
    }
}
