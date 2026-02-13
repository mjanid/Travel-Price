import Foundation

/// ViewModel for trips list and CRUD operations.
@Observable
final class TripsViewModel {
    var trips: [Trip] = []
    var selectedTrip: Trip?
    var currentPage = 1
    var totalPages = 1
    var total = 0
    var isLoading = false
    var error: String?
    var scrapeResult: [PriceSnapshot]?
    var isScraping = false

    private let api: APIClient
    private let perPage = 20

    init(api: APIClient) {
        self.api = api
    }

    // MARK: - Fetch

    @MainActor
    func fetchTrips(page: Int = 1) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let query = ["page": "\(page)", "per_page": "\(perPage)"]
            let response: PaginatedResponse<Trip> = try await api.get(
                APIEndpoints.trips, query: query
            )
            trips = response.data
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
    func fetchTrip(id: String) async {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<Trip> = try await api.get(APIEndpoints.trip(id))
            selectedTrip = response.data
        } catch let apiError as APIError {
            error = apiError.localizedDescription
        } catch {
            self.error = error.localizedDescription
        }
    }

    // MARK: - CRUD

    @MainActor
    func createTrip(_ request: TripCreateRequest) async -> Trip? {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<Trip> = try await api.post(
                APIEndpoints.trips, body: request
            )
            if let trip = response.data {
                await fetchTrips(page: 1)
                return trip
            }
            error = response.errors?.first ?? "Failed to create trip"
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
    func updateTrip(id: String, _ request: TripUpdateRequest) async -> Bool {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            let response: ApiResponse<Trip> = try await api.patch(
                APIEndpoints.trip(id), body: request
            )
            if let trip = response.data {
                selectedTrip = trip
                return true
            }
            error = response.errors?.first ?? "Failed to update trip"
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
    func deleteTrip(id: String) async -> Bool {
        isLoading = true
        error = nil
        defer { isLoading = false }

        do {
            try await api.delete(APIEndpoints.trip(id))
            trips.removeAll { $0.id == id }
            return true
        } catch let apiError as APIError {
            error = apiError.localizedDescription
            return false
        } catch {
            self.error = error.localizedDescription
            return false
        }
    }

    // MARK: - Scrape

    @MainActor
    func scrapeTrip(id: String) async {
        isScraping = true
        scrapeResult = nil
        error = nil
        defer { isScraping = false }

        do {
            let response: ApiResponse<[PriceSnapshot]> = try await api.post(
                APIEndpoints.tripScrape(id)
            )
            scrapeResult = response.data
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
        await fetchTrips(page: currentPage + 1)
    }

    @MainActor
    func previousPage() async {
        guard currentPage > 1 else { return }
        await fetchTrips(page: currentPage - 1)
    }
}
