import Foundation
import SwiftUI

/// Manages authentication state for the entire app.
@Observable
final class AuthViewModel {
    var currentUser: User?
    var isAuthenticated = false
    var isLoading = false
    var error: String?

    private let api: APIClient

    init(api: APIClient) {
        self.api = api
        api.onAuthFailure = { [weak self] in
            Task { @MainActor in
                self?.logout()
            }
        }
    }

    // MARK: - Auth Actions

    /// Check for existing session on app launch.
    @MainActor
    func checkSession() async {
        guard await TokenManager.shared.hasTokens else { return }
        isLoading = true
        defer { isLoading = false }

        do {
            let response: ApiResponse<User> = try await api.get(APIEndpoints.me)
            if let user = response.data {
                currentUser = user
                isAuthenticated = true
            }
        } catch {
            // Token invalid — clear and stay logged out
            await TokenManager.shared.clearTokens()
        }
    }

    @MainActor
    func login(email: String, password: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let body = LoginRequest(email: email, password: password)
            let response: ApiResponse<TokenResponse> = try await api.post(APIEndpoints.login, body: body)

            guard let tokens = response.data else {
                error = response.errors?.first ?? "Login failed"
                return
            }

            await TokenManager.shared.saveTokens(
                accessToken: tokens.accessToken,
                refreshToken: tokens.refreshToken
            )

            // Fetch user profile
            let userResponse: ApiResponse<User> = try await api.get(APIEndpoints.me)
            currentUser = userResponse.data
            isAuthenticated = true
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    @MainActor
    func register(email: String, password: String, fullName: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let body = RegisterRequest(email: email, password: password, fullName: fullName)
            let _: ApiResponse<User> = try await api.post(APIEndpoints.register, body: body)

            // Auto-login after registration
            await login(email: email, password: password)
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    @MainActor
    func updateProfile(fullName: String? = nil, password: String? = nil) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let body = UpdateProfileRequest(fullName: fullName, password: password)
            let response: ApiResponse<User> = try await api.patch(APIEndpoints.me, body: body)
            if let user = response.data {
                currentUser = user
            }
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    @MainActor
    func logout() {
        Task {
            await TokenManager.shared.clearTokens()
        }
        currentUser = nil
        isAuthenticated = false
        error = nil
    }
}
