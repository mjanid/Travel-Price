import Foundation

/// ViewModel for fetching price snapshots.
@Observable
final class PriceHistoryViewModel {
    var snapshots: [PriceSnapshot] = []
    var currentPage = 1
    var totalPages = 1
    var isLoading = false
    var error: String?

    private let api: APIClient
    private let perPage = 50

    init(api: APIClient) {
        self.api = api
    }

    @MainActor
    func fetchPrices(tripId: String, provider: String? = nil, page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            var query = ["page": "\(page)", "per_page": "\(perPage)"]
            if let provider {
                query["provider"] = provider
            }
            let response: PaginatedResponse<PriceSnapshot> = try await api.get(
                APIEndpoints.tripPrices(tripId), query: query
            )
            snapshots = response.data
            currentPage = response.meta.page
            totalPages = response.meta.totalPages
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }
}
