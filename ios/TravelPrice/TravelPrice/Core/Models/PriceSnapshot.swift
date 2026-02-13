import Foundation

struct PriceSnapshot: Codable, Identifiable {
    let id: String
    let tripId: String
    let provider: String
    let price: Int
    let currency: String
    let cabinClass: String?
    let airline: String?
    let outboundDeparture: String?
    let outboundArrival: String?
    let returnDeparture: String?
    let returnArrival: String?
    let stops: Int?
    let rawData: String?
    let scrapedAt: String
    let createdAt: String

    /// Decoded raw_data JSON dictionary.
    var rawDataDict: [String: String]? {
        guard let rawData, let data = rawData.data(using: .utf8) else { return nil }
        return try? JSONDecoder().decode([String: String].self, from: data)
    }

    /// Price in dollars (convenience).
    var priceInDollars: Double {
        Double(price) / 100.0
    }

    // MARK: - Display helpers (prefer raw_data values, fall back to top-level fields)

    /// Airline name for display. Uses top-level `airline` first, then `raw_data.airline`.
    var displayAirline: String {
        airline ?? rawDataDict?["airline"] ?? "—"
    }

    /// Departure time string from raw_data (e.g. "3:05 PM").
    var displayDepartureTime: String {
        rawDataDict?["departure_time"] ?? "—"
    }

    /// Arrival time string from raw_data (e.g. "4:20 PM").
    var displayArrivalTime: String {
        rawDataDict?["arrival_time"] ?? "—"
    }

    /// Duration string from raw_data (e.g. "1 hr 15 min").
    var displayDuration: String {
        rawDataDict?["duration"] ?? "—"
    }

    /// Stops for display. Uses top-level `stops` first, then `raw_data.stops`.
    var displayStops: String {
        if let s = stops { return s == 0 ? "Direct" : "\(s)" }
        if let s = rawDataDict?["stops"] { return s }
        return "—"
    }
}
