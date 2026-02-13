import Foundation

/// All backend API endpoint paths.
enum APIEndpoints {
    // MARK: - Auth
    static let register = "/api/v1/auth/register"
    static let login = "/api/v1/auth/login"
    static let refresh = "/api/v1/auth/refresh"
    static let me = "/api/v1/auth/me"

    // MARK: - Trips
    static let trips = "/api/v1/trips/"
    static func trip(_ id: String) -> String { "/api/v1/trips/\(id)" }
    static func tripScrape(_ id: String) -> String { "/api/v1/trips/\(id)/scrape" }
    static func tripPrices(_ id: String) -> String { "/api/v1/trips/\(id)/prices" }
    static func tripWatches(_ id: String) -> String { "/api/v1/trips/\(id)/watches" }

    // MARK: - Watches
    static let watches = "/api/v1/watches/"
    static func watch(_ id: String) -> String { "/api/v1/watches/\(id)" }
    static func watchAlerts(_ id: String) -> String { "/api/v1/watches/\(id)/alerts" }

    // MARK: - Alerts
    static let alerts = "/api/v1/alerts/"
    static func alert(_ id: String) -> String { "/api/v1/alerts/\(id)" }

    // MARK: - Health
    static let health = "/health"
}
