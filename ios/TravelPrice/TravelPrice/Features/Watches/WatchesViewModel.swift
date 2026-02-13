import Foundation

/// ViewModel for price watches.
@Observable
final class WatchesViewModel {
    var watches: [PriceWatch] = []
    var selectedWatch: PriceWatch?
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

    // MARK: - Fetch

    @MainActor
    func fetchWatches(page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let query = ["page": "\(page)", "per_page": "\(perPage)"]
            let response: PaginatedResponse<PriceWatch> = try await api.get(
                APIEndpoints.watches, query: query
            )
            watches = response.data
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
    func fetchTripWatches(tripId: String, page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let query = ["page": "\(page)", "per_page": "\(perPage)"]
            let response: PaginatedResponse<PriceWatch> = try await api.get(
                APIEndpoints.tripWatches(tripId), query: query
            )
            watches = response.data
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
    func fetchWatch(id: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<PriceWatch> = try await api.get(
                APIEndpoints.watch(id)
            )
            selectedWatch = response.data
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: - CRUD

    @MainActor
    func createWatch(_ request: WatchCreateRequest) async -> PriceWatch? {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<PriceWatch> = try await api.post(
                APIEndpoints.watches, body: request
            )
            if let watch = response.data {
                return watch
            }
            error = response.errors?.first ?? "Failed to create watch"
            return nil
        } catch let apiError as APIError {
            error = apiError.localizedDescription
            return nil
        } catch {
            self.error = error.localizedDescription
            return nil
        }
    }

    @MainActor
    func updateWatch(id: String, _ request: WatchUpdateRequest) async -> Bool {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<PriceWatch> = try await api.patch(
                APIEndpoints.watch(id), body: request
            )
            if let watch = response.data {
                selectedWatch = watch
                return true
            }
            error = response.errors?.first ?? "Failed to update watch"
            return false
        } catch let apiError as APIError {
            error = apiError.localizedDescription
            return false
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    @MainActor
    func toggleActive(id: String, currentlyActive: Bool) async -> Bool {
        let request = WatchUpdateRequest(isActive: !currentlyActive)
        return await updateWatch(id: id, request)
    }

    @MainActor
    func deleteWatch(id: String) async -> Bool {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            try await api.delete(APIEndpoints.watch(id))
            watches.removeAll { $0.id == id }
            return true
        } catch let apiError as APIError {
            error = apiError.localizedDescription
            return false
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    // MARK: - Pagination

    @MainActor
    func nextPage() async {
        guard currentPage < totalPages else { return }
        await fetchWatches(page: currentPage + 1)
    }

    @MainActor
    func previousPage() async {
        guard currentPage > 1 else { return }
        await fetchWatches(page: currentPage - 1)
    }
}
