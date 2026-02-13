import Foundation

/// Centralized HTTP client for all backend API calls.
///
/// Manages base URL configuration, JWT authorization headers,
/// automatic 401 token refresh, and JSON encoding/decoding.
@Observable
final class APIClient {
    // MARK: - Configuration

    var baseURL: String {
        didSet { UserDefaults.standard.set(baseURL, forKey: "api_base_url") }
    }

    /// Callback invoked when token refresh fails — triggers logout in AuthViewModel.
    var onAuthFailure: (() -> Void)?

    private let session: URLSession
    private let decoder: JSONDecoder
    private let encoder: JSONEncoder
    private var isRefreshing = false

    // MARK: - Init

    init() {
        self.baseURL = UserDefaults.standard.string(forKey: "api_base_url")
            ?? "http://localhost:8000"

        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 30
        config.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: config)

        self.decoder = JSONDecoder()
        self.decoder.keyDecodingStrategy = .convertFromSnakeCase
        self.decoder.dateDecodingStrategy = .iso8601

        self.encoder = JSONEncoder()
        self.encoder.keyEncodingStrategy = .convertToSnakeCase
    }

    // MARK: - Public Methods

    func get<T: Decodable>(_ path: String, query: [String: String]? = nil) async throws -> T {
        let request = try buildRequest(path: path, method: "GET", query: query)
        return try await perform(request)
    }

    func post<T: Decodable>(_ path: String, body: (any Encodable)? = nil) async throws -> T {
        let request = try buildRequest(path: path, method: "POST", body: body)
        return try await perform(request)
    }

    func patch<T: Decodable>(_ path: String, body: any Encodable) async throws -> T {
        let request = try buildRequest(path: path, method: "PATCH", body: body)
        return try await perform(request)
    }

    func delete(_ path: String) async throws {
        let request = try buildRequest(path: path, method: "DELETE")
        let (_, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIError.networkError(URLError(.badServerResponse)) }

        if http.statusCode == 401 {
            if try await refreshAndRetry(request) { return }
            throw APIError.unauthorized
        }
        guard (200...299).contains(http.statusCode) else {
            throw APIError.httpError(statusCode: http.statusCode, message: "Delete failed")
        }
    }

    /// Test connection by hitting the `/health` endpoint.
    func testConnection() async throws -> Bool {
        let request = try buildRequest(path: APIEndpoints.health, method: "GET")
        let (_, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else { return false }
        return http.statusCode == 200
    }

    // MARK: - Request Building

    private func buildRequest(
        path: String,
        method: String,
        query: [String: String]? = nil,
        body: (any Encodable)? = nil
    ) throws -> URLRequest {
        guard var components = URLComponents(string: baseURL + path) else {
            throw APIError.invalidURL
        }

        if let query, !query.isEmpty {
            components.queryItems = query.map { URLQueryItem(name: $0.key, value: $0.value) }
        }

        guard let url = components.url else { throw APIError.invalidURL }

        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let body {
            request.httpBody = try encoder.encode(AnyEncodable(body))
        }

        return request
    }

    /// Attach Bearer token from Keychain.
    private func authorizeRequest(_ request: inout URLRequest) async {
        if let token = await TokenManager.shared.getAccessToken() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
    }

    // MARK: - Request Execution

    private func perform<T: Decodable>(_ request: URLRequest) async throws -> T {
        var authedRequest = request
        await authorizeRequest(&authedRequest)

        let (data, response) = try await execute(authedRequest)
        let http = response

        // 401 → try token refresh once
        if http.statusCode == 401 {
            if let refreshed: T = try await refreshAndRetryWithResult(request) {
                return refreshed
            }
            throw APIError.unauthorized
        }

        guard (200...299).contains(http.statusCode) else {
            // Try to extract error messages from response
            if let apiResponse = try? decoder.decode(ApiResponse<EmptyData>.self, from: data),
               let errors = apiResponse.errors, !errors.isEmpty {
                throw APIError.serverErrors(errors)
            }
            throw APIError.httpError(statusCode: http.statusCode, message: nil)
        }

        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIError.decodingError(error)
        }
    }

    private func execute(_ request: URLRequest) async throws -> (Data, HTTPURLResponse) {
        do {
            let (data, response) = try await session.data(for: request)
            guard let http = response as? HTTPURLResponse else {
                throw APIError.networkError(URLError(.badServerResponse))
            }
            return (data, http)
        } catch let error as APIError {
            throw error
        } catch {
            throw APIError.networkError(error)
        }
    }

    // MARK: - Token Refresh

    private func refreshAndRetry(_ originalRequest: URLRequest) async throws -> Bool {
        guard !isRefreshing else { return false }
        isRefreshing = true
        defer { isRefreshing = false }

        guard let refreshToken = await TokenManager.shared.getRefreshToken() else {
            await handleAuthFailure()
            return false
        }

        do {
            let body = RefreshRequest(refreshToken: refreshToken)
            let bodyData = try encoder.encode(body)

            guard let url = URL(string: baseURL + APIEndpoints.refresh) else { return false }
            var refreshReq = URLRequest(url: url)
            refreshReq.httpMethod = "POST"
            refreshReq.setValue("application/json", forHTTPHeaderField: "Content-Type")
            refreshReq.httpBody = bodyData

            let (data, response) = try await execute(refreshReq)
            guard response.statusCode == 200 else {
                await handleAuthFailure()
                return false
            }

            let tokenResponse = try decoder.decode(ApiResponse<TokenResponse>.self, from: data)
            guard let tokens = tokenResponse.data else {
                await handleAuthFailure()
                return false
            }

            await TokenManager.shared.saveTokens(
                accessToken: tokens.accessToken,
                refreshToken: tokens.refreshToken
            )

            // Retry original request
            var retryRequest = originalRequest
            await authorizeRequest(&retryRequest)
            let (_, retryResponse) = try await execute(retryRequest)
            return (200...299).contains(retryResponse.statusCode)
        } catch {
            await handleAuthFailure()
            return false
        }
    }

    private func refreshAndRetryWithResult<T: Decodable>(_ originalRequest: URLRequest) async throws -> T? {
        guard !isRefreshing else { return nil }
        isRefreshing = true
        defer { isRefreshing = false }

        guard let refreshToken = await TokenManager.shared.getRefreshToken() else {
            await handleAuthFailure()
            return nil
        }

        do {
            let body = RefreshRequest(refreshToken: refreshToken)
            let bodyData = try encoder.encode(body)

            guard let url = URL(string: baseURL + APIEndpoints.refresh) else { return nil }
            var refreshReq = URLRequest(url: url)
            refreshReq.httpMethod = "POST"
            refreshReq.setValue("application/json", forHTTPHeaderField: "Content-Type")
            refreshReq.httpBody = bodyData

            let (data, response) = try await execute(refreshReq)
            guard response.statusCode == 200 else {
                await handleAuthFailure()
                return nil
            }

            let tokenResponse = try decoder.decode(ApiResponse<TokenResponse>.self, from: data)
            guard let tokens = tokenResponse.data else {
                await handleAuthFailure()
                return nil
            }

            await TokenManager.shared.saveTokens(
                accessToken: tokens.accessToken,
                refreshToken: tokens.refreshToken
            )

            // Retry original request
            var retryRequest = originalRequest
            await authorizeRequest(&retryRequest)
            let (retryData, retryResponse) = try await execute(retryRequest)
            guard (200...299).contains(retryResponse.statusCode) else { return nil }
            return try decoder.decode(T.self, from: retryData)
        } catch {
            await handleAuthFailure()
            return nil
        }
    }

    @MainActor
    private func handleAuthFailure() {
        onAuthFailure?()
    }
}

// MARK: - Helpers

/// Type-erased Encodable wrapper for generic encoding.
private struct AnyEncodable: Encodable {
    private let _encode: (Encoder) throws -> Void

    init(_ value: any Encodable) {
        _encode = { encoder in try value.encode(to: encoder) }
    }

    func encode(to encoder: Encoder) throws {
        try _encode(encoder)
    }
}

/// Empty placeholder for decoding error responses without a data field.
struct EmptyData: Decodable {}

/// Request body for token refresh.
private struct RefreshRequest: Encodable {
    let refreshToken: String
}
