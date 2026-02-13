import Foundation

/// Generic API response envelope: `{ data, meta, errors }`.
struct ApiResponse<T: Decodable>: Decodable {
    let data: T?
    let meta: ResponseMeta?
    let errors: [String]?
}

/// Paginated API response: `{ data: [...], meta: { page, per_page, total, total_pages }, errors }`.
struct PaginatedResponse<T: Decodable>: Decodable {
    let data: [T]
    let meta: PaginationMeta
    let errors: [String]?
}

struct ResponseMeta: Decodable {
    let requestId: String?
}

struct PaginationMeta: Decodable {
    let page: Int
    let perPage: Int
    let total: Int
    let totalPages: Int
}

/// Auth token response from login/refresh.
struct TokenResponse: Decodable {
    let accessToken: String
    let refreshToken: String
    let tokenType: String
}
