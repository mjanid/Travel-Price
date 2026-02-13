import SwiftUI

struct DashboardView: View {
    @Environment(APIClient.self) private var api
    @Environment(AuthViewModel.self) private var auth

    @State private var tripsVM: TripsViewModel?
    @State private var watchesVM: WatchesViewModel?
    @State private var alertsVM: AlertsViewModel?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 20) {
                    // Welcome
                    if let user = auth.currentUser {
                        Text("Welcome, \(user.fullName)")
                            .font(.title2)
                            .fontWeight(.bold)
                            .padding(.horizontal)
                    }

                    // Stats cards
                    statsSection

                    // Recent trips
                    if let tripsVM {
                        sectionHeader("Recent Trips")
                        if tripsVM.trips.isEmpty {
                            Text("No trips yet. Create your first trip!")
                                .font(.subheadline)
                                .foregroundStyle(.secondary)
                                .padding(.horizontal)
                        } else {
                            ForEach(tripsVM.trips.prefix(4)) { trip in
                                NavigationLink(value: trip.id) {
                                    TripCardView(trip: trip)
                                }
                                .buttonStyle(.plain)
                                .padding(.horizontal)
                            }
                        }
                    }

                    // Recent alerts
                    if let alertsVM, !alertsVM.alerts.isEmpty {
                        sectionHeader("Recent Alerts")
                        ForEach(alertsVM.alerts.prefix(3)) { alert in
                            alertCard(alert)
                                .padding(.horizontal)
                        }
                    }
                }
                .padding(.vertical)
            }
            .navigationTitle("Dashboard")
            .refreshable {
                await loadData()
            }
            .navigationDestination(for: String.self) { tripId in
                TripDetailView(tripId: tripId)
            }
            .task {
                if tripsVM == nil { tripsVM = TripsViewModel(api: api) }
                if watchesVM == nil { watchesVM = WatchesViewModel(api: api) }
                if alertsVM == nil { alertsVM = AlertsViewModel(api: api) }
                await loadData()
            }
        }
    }

    // MARK: - Stats

    private var statsSection: some View {
        LazyVGrid(columns: [
            GridItem(.flexible()),
            GridItem(.flexible()),
            GridItem(.flexible()),
        ], spacing: 12) {
            statCard(
                title: "Trips",
                value: "\(tripsVM?.total ?? 0)",
                icon: "airplane",
                color: .blue
            )
            statCard(
                title: "Watches",
                value: "\(watchesVM?.total ?? 0)",
                icon: "eye.fill",
                color: .purple
            )
            statCard(
                title: "Alerts",
                value: "\(alertsVM?.total ?? 0)",
                icon: "bell.fill",
                color: .orange
            )
        }
        .padding(.horizontal)
    }

    private func statCard(title: String, value: String, icon: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.title2)
                .foregroundStyle(color)
            Text(value)
                .font(.title)
                .fontWeight(.bold)
            Text(title)
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .frame(maxWidth: .infinity)
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }

    // MARK: - Helpers

    private func sectionHeader(_ title: String) -> some View {
        Text(title)
            .font(.headline)
            .padding(.horizontal)
    }

    private func alertCard(_ alert: PriceAlert) -> some View {
        HStack {
            Image(systemName: "bell.fill")
                .foregroundStyle(.orange)
            VStack(alignment: .leading, spacing: 2) {
                Text("Price drop: \(Formatters.price(cents: alert.triggeredPrice))")
                    .font(.subheadline)
                    .fontWeight(.medium)
                Text("Target: \(Formatters.price(cents: alert.targetPrice))")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Text(Formatters.displayDate(alert.createdAt))
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .shadow(color: .black.opacity(0.04), radius: 3, y: 1)
    }

    private func loadData() async {
        await tripsVM?.fetchTrips()
        await watchesVM?.fetchWatches()
        await alertsVM?.fetchAlerts()
    }
}
