import Foundation
import Security

/// Thread-safe Keychain-based JWT token storage.
actor TokenManager {
    static let shared = TokenManager()

    private let accessTokenKey = "com.travelprice.accessToken"
    private let refreshTokenKey = "com.travelprice.refreshToken"

    private init() {}

    // MARK: - Public API

    func saveTokens(accessToken: String, refreshToken: String) {
        save(key: accessTokenKey, value: accessToken)
        save(key: refreshTokenKey, value: refreshToken)
    }

    func getAccessToken() -> String? {
        load(key: accessTokenKey)
    }

    func getRefreshToken() -> String? {
        load(key: refreshTokenKey)
    }

    func clearTokens() {
        delete(key: accessTokenKey)
        delete(key: refreshTokenKey)
    }

    var hasTokens: Bool {
        getAccessToken() != nil
    }

    // MARK: - Keychain Helpers

    private func save(key: String, value: String) {
        guard let data = value.data(using: .utf8) else { return }
        delete(key: key) // Remove existing before saving

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock,
        ]
        SecItemAdd(query as CFDictionary, nil)
    }

    private func load(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    private func delete(key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
