import Foundation

enum Validators {
    /// Validate email format.
    static func isValidEmail(_ email: String) -> Bool {
        let pattern = #"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$"#
        return email.range(of: pattern, options: .regularExpression) != nil
    }

    /// Validate password (8+ characters).
    static func isValidPassword(_ password: String) -> Bool {
        password.count >= 8
    }

    /// Validate IATA code (exactly 3 alphabetic characters).
    static func isValidIATA(_ code: String) -> Bool {
        let trimmed = code.trimmingCharacters(in: .whitespaces)
        return trimmed.count == 3 && trimmed.allSatisfy(\.isLetter)
    }

    /// Validate full name (1-255 characters).
    static func isValidFullName(_ name: String) -> Bool {
        let trimmed = name.trimmingCharacters(in: .whitespaces)
        return !trimmed.isEmpty && trimmed.count <= 255
    }

    /// Validate notes (max 2000 characters).
    static func isValidNotes(_ notes: String) -> Bool {
        notes.count <= 2000
    }

    /// Validate target price in dollars (must be > 0).
    static func isValidTargetPrice(_ dollars: String) -> Bool {
        guard let cents = Formatters.dollarsToCents(dollars) else { return false }
        return cents > 0
    }
}
