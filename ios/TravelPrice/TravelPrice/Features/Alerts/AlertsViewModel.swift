import Foundation

/// ViewModel for alerts.
@Observable
final class AlertsViewModel {
    var alerts: [PriceAlert] = []
    var currentPage = 1
    var totalPages = 1
    var total = 0
    var isLoading = false
    var error: String?

    private let api: APIClient
    private let perPage = 20

    init(api: APIClient) {
        self.api = api
    }

    @MainActor
    func fetchAlerts(page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let query = ["page": "\(page)", "per_page": "\(perPage)"]
            let response: PaginatedResponse<PriceAlert> = try await api.get(
                APIEndpoints.alerts, query: query
            )
            alerts = response.data
            currentPage = response.meta.page
            totalPages = response.meta.totalPages
            total = response.meta.total
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    @MainActor
    func fetchWatchAlerts(watchId: String, page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let query = ["page": "\(page)", "per_page": "\(perPage)"]
            let response: PaginatedResponse<PriceAlert> = try await api.get(
                APIEndpoints.watchAlerts(watchId), query: query
            )
            alerts = response.data
            currentPage = response.meta.page
            totalPages = response.meta.totalPages
            total = response.meta.total
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: - Pagination

    @MainActor
    func nextPage() async {
        guard currentPage < totalPages else { return }
        await fetchAlerts(page: currentPage + 1)
    }

    @MainActor
    func previousPage() async {
        guard currentPage > 1 else { return }
        await fetchAlerts(page: currentPage - 1)
    }
}
