import SwiftUI

struct TripDetailView: View {
    @Environment(APIClient.self) private var api
    @Environment(\.dismiss) private var dismiss
    let tripId: String

    @State private var viewModel: TripsViewModel?
    @State private var priceVM: PriceHistoryViewModel?
    @State private var watchVM: WatchesViewModel?
    @State private var showEditSheet = false
    @State private var showDeleteAlert = false
    @State private var showAddWatch = false

    private var trip: Trip? { viewModel?.selectedTrip }

    var body: some View {
        Group {
            if let trip {
                tripDetail(trip)
            } else if viewModel?.isLoading == true {
                LoadingView()
            } else if let error = viewModel?.error {
                ErrorView(message: error) {
                    Task { await viewModel?.fetchTrip(id: tripId) }
                }
            } else {
                LoadingView()
            }
        }
        .navigationTitle(trip.map { "\($0.origin) → \($0.destination)" } ?? "Trip")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .task {
            if viewModel == nil { viewModel = TripsViewModel(api: api) }
            if priceVM == nil { priceVM = PriceHistoryViewModel(api: api) }
            if watchVM == nil { watchVM = WatchesViewModel(api: api) }
            await viewModel?.fetchTrip(id: tripId)
            await priceVM?.fetchPrices(tripId: tripId)
            await watchVM?.fetchTripWatches(tripId: tripId)
        }
    }

    @ViewBuilder
    private func tripDetail(_ trip: Trip) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Header card
                tripHeader(trip)

                // Action buttons
                actionButtons(trip)

                // Price chart
                if let priceVM, !priceVM.snapshots.isEmpty {
                    sectionHeader("Price History")
                    PriceChartView(snapshots: priceVM.snapshots)
                        .frame(height: 200)
                        .padding(.horizontal)
                }

                // Flight results
                if trip.tripType == "flight", let priceVM, !priceVM.snapshots.isEmpty {
                    sectionHeader("Recent Flight Results")
                    FlightResultsView(snapshots: priceVM.snapshots)
                        .padding(.horizontal)
                }

                // Price watches
                if let watchVM {
                    HStack {
                        sectionHeader("Price Watches")
                        Spacer()
                        Button {
                            showAddWatch = true
                        } label: {
                            Label("Add", systemImage: "plus.circle")
                                .font(.subheadline)
                        }
                        .padding(.trailing)
                    }

                    if watchVM.watches.isEmpty {
                        Text("No price watches yet. Add one to get alerts.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .padding(.horizontal)
                    } else {
                        ForEach(watchVM.watches) { watch in
                            WatchCardView(watch: watch)
                                .padding(.horizontal)
                        }
                    }
                }
            }
            .padding(.vertical)
        }
        .refreshable {
            await viewModel?.fetchTrip(id: tripId)
            await priceVM?.fetchPrices(tripId: tripId)
            await watchVM?.fetchTripWatches(tripId: tripId)
        }
        .sheet(isPresented: $showEditSheet) {
            if let vm = viewModel {
                TripFormView(viewModel: vm, editingTrip: trip)
            }
        }
        .sheet(isPresented: $showAddWatch) {
            if let watchVM {
                WatchFormView(viewModel: watchVM, tripId: tripId)
            }
        }
        .alert("Delete Trip?", isPresented: $showDeleteAlert) {
            Button("Delete", role: .destructive) {
                Task {
                    let success = await viewModel?.deleteTrip(id: tripId) ?? false
                    if success { dismiss() }
                }
            }
            Button("Cancel", role: .cancel) {}
        } message: {
            Text("This will permanently delete the trip and all associated data.")
        }
    }

    // MARK: - Subviews

    private func tripHeader(_ trip: Trip) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: (TripType(rawValue: trip.tripType) ?? .flight).icon)
                    .font(.title2)
                    .foregroundStyle(.blue)
                VStack(alignment: .leading) {
                    Text("\(trip.origin) → \(trip.destination)")
                        .font(.title2)
                        .fontWeight(.bold)
                    Text((TripType(rawValue: trip.tripType) ?? .flight).displayName)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
                Spacer()
                StatusBadge(
                    text: isPast(trip) ? "Past" : "Upcoming",
                    variant: isPast(trip) ? .default : .success
                )
            }

            Divider()

            HStack(spacing: 24) {
                Label(Formatters.displayDate(trip.departureDate), systemImage: "calendar")
                if let returnDate = trip.returnDate {
                    Label(Formatters.displayDate(returnDate), systemImage: "calendar.badge.clock")
                }
            }
            .font(.subheadline)
            .foregroundStyle(.secondary)

            Label("\(trip.travelers) traveler\(trip.travelers == 1 ? "" : "s")", systemImage: "person.fill")
                .font(.subheadline)
                .foregroundStyle(.secondary)

            if let notes = trip.notes, !notes.isEmpty {
                Text(notes)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
        .padding(.horizontal)
    }

    private func actionButtons(_ trip: Trip) -> some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 12) {
                Button {
                    showEditSheet = true
                } label: {
                    Label("Edit", systemImage: "pencil")
                }
                .buttonStyle(.bordered)

                Button {
                    Task { await viewModel?.scrapeTrip(id: trip.id) }
                } label: {
                    if viewModel?.isScraping == true {
                        ProgressView()
                    } else {
                        Label("Scrape Now", systemImage: "arrow.clockwise")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(viewModel?.isScraping == true)

                Button(role: .destructive) {
                    showDeleteAlert = true
                } label: {
                    Label("Delete", systemImage: "trash")
                }
                .buttonStyle(.bordered)
            }
            .padding(.horizontal)
        }
    }

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.headline)
            .padding(.horizontal)
    }

    private func isPast(_ trip: Trip) -> Bool {
        guard let date = Formatters.parseDate(trip.departureDate) else { return false }
        return date < Date()
    }
}
