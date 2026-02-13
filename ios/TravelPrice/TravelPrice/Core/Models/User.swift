import Foundation

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let fullName: String
    let isActive: Bool
    let createdAt: String
}

// MARK: - Request Models

struct LoginRequest: Encodable {
    let email: String
    let password: String
}

struct RegisterRequest: Encodable {
    let email: String
    let password: String
    let fullName: String
}

struct UpdateProfileRequest: Encodable {
    let fullName: String?
    let password: String?

    init(fullName: String? = nil, password: String? = nil) {
        self.fullName = fullName
        self.password = password
    }
}
