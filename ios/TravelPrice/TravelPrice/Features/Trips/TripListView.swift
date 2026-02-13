import SwiftUI

struct TripListView: View {
    @Environment(APIClient.self) private var api
    @State private var viewModel: TripsViewModel?
    @State private var showCreateForm = false

    var body: some View {
        NavigationStack {
            Group {
                if let vm = viewModel {
                    tripContent(vm)
                } else {
                    LoadingView()
                }
            }
            .navigationTitle("Trips")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        showCreateForm = true
                    } label: {
                        Label("New Trip", systemImage: "plus")
                    }
                }
            }
            .sheet(isPresented: $showCreateForm) {
                if let vm = viewModel {
                    TripFormView(viewModel: vm)
                }
            }
            .task {
                if viewModel == nil {
                    viewModel = TripsViewModel(api: api)
                }
                await viewModel?.fetchTrips()
            }
        }
    }

    @ViewBuilder
    private func tripContent(_ vm: TripsViewModel) -> some View {
        if vm.isLoading && vm.trips.isEmpty {
            LoadingView()
        } else if let error = vm.error, vm.trips.isEmpty {
            ErrorView(message: error) {
                Task { await vm.fetchTrips() }
            }
        } else if vm.trips.isEmpty {
            emptyState
        } else {
            List {
                ForEach(vm.trips) { trip in
                    NavigationLink(value: trip.id) {
                        TripCardView(trip: trip)
                    }
                    .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                    .listRowSeparator(.hidden)
                }

                if vm.totalPages > 1 {
                    PaginationControls(
                        currentPage: vm.currentPage,
                        totalPages: vm.totalPages,
                        onPrevious: { Task { await vm.previousPage() } },
                        onNext: { Task { await vm.nextPage() } }
                    )
                    .listRowSeparator(.hidden)
                }
            }
            .listStyle(.plain)
            .refreshable {
                await vm.fetchTrips(page: vm.currentPage)
            }
            .navigationDestination(for: String.self) { tripId in
                TripDetailView(tripId: tripId)
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "airplane.departure")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("No Trips Yet")
                .font(.title3)
                .fontWeight(.semibold)
            Text("Create your first trip to start tracking prices.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
            Button("Create Trip") {
                showCreateForm = true
            }
            .buttonStyle(.borderedProminent)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
