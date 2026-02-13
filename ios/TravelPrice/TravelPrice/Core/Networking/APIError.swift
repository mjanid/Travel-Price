import Foundation

/// All possible errors from the API layer.
enum APIError: LocalizedError {
    case invalidURL
    case networkError(Error)
    case httpError(statusCode: Int, message: String?)
    case decodingError(Error)
    case unauthorized
    case serverErrors([String])
    case noData
    case tokenRefreshFailed

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid server URL. Check your settings."
        case .networkError(let error):
            return "Network error: \(error.localizedDescription)"
        case .httpError(let code, let message):
            return message ?? "Server error (\(code))"
        case .decodingError:
            return "Failed to process server response."
        case .unauthorized:
            return "Session expired. Please log in again."
        case .serverErrors(let errors):
            return errors.joined(separator: "\n")
        case .noData:
            return "No data received from server."
        case .tokenRefreshFailed:
            return "Session expired. Please log in again."
        }
    }
}
