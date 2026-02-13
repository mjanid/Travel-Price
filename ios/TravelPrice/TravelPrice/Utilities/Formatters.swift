import Foundation

enum Formatters {
    // MARK: - Price

    /// Format cents to display string, e.g. 12345 → "$123.45".
    static func price(cents: Int, currency: String = "USD") -> String {
        let dollars = Double(cents) / 100.0
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.currencyCode = currency
        formatter.maximumFractionDigits = 2
        formatter.minimumFractionDigits = 2
        return formatter.string(from: NSNumber(value: dollars)) ?? "$\(String(format: "%.2f", dollars))"
    }

    /// Parse dollar string (e.g. "123.45") to cents (12345).
    static func dollarsToCents(_ dollars: String) -> Int? {
        let cleaned = dollars.replacingOccurrences(of: "$", with: "")
            .replacingOccurrences(of: ",", with: "")
            .trimmingCharacters(in: .whitespaces)
        guard let value = Double(cleaned) else { return nil }
        return Int(round(value * 100))
    }

    // MARK: - Dates

    private static let isoFormatter: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()

    private static let isoFormatterNoFrac: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        return f
    }()

    private static let displayDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .none
        return f
    }()

    private static let displayDateTimeFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateStyle = .medium
        f.timeStyle = .short
        return f
    }()

    private static let apiDateFormatter: DateFormatter = {
        let f = DateFormatter()
        f.dateFormat = "yyyy-MM-dd"
        f.locale = Locale(identifier: "en_US_POSIX")
        return f
    }()

    /// Parse ISO 8601 string to Date.
    static func parseISO(_ string: String) -> Date? {
        isoFormatter.date(from: string) ?? isoFormatterNoFrac.date(from: string)
    }

    /// Parse date-only string (yyyy-MM-dd) to Date.
    static func parseDate(_ string: String) -> Date? {
        apiDateFormatter.date(from: string)
    }

    /// Format ISO 8601 string to display date, e.g. "Jun 15, 2026".
    static func displayDate(_ isoString: String) -> String {
        // Handle date-only strings (yyyy-MM-dd)
        if let date = parseDate(isoString) {
            return displayDateFormatter.string(from: date)
        }
        guard let date = parseISO(isoString) else { return isoString }
        return displayDateFormatter.string(from: date)
    }

    /// Format ISO 8601 string to display date+time, e.g. "Jun 15, 2026 at 3:45 PM".
    static func displayDateTime(_ isoString: String) -> String {
        guard let date = parseISO(isoString) else { return isoString }
        return displayDateTimeFormatter.string(from: date)
    }

    /// Format Date to API date string (yyyy-MM-dd).
    static func apiDate(_ date: Date) -> String {
        apiDateFormatter.string(from: date)
    }

    // MARK: - IATA

    /// Normalize IATA code: uppercase, trimmed, max 3 chars.
    static func iataCode(_ code: String) -> String {
        String(code.uppercased().trimmingCharacters(in: .whitespaces).prefix(3))
    }
}
