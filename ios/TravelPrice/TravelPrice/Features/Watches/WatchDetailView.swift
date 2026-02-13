import SwiftUI

struct WatchDetailView: View {
    @Environment(APIClient.self) private var api
    @Environment(\.dismiss) private var dismiss
    let watchId: String

    @State private var viewModel: WatchesViewModel?
    @State private var alertsVM: AlertsViewModel?
    @State private var priceVM: PriceHistoryViewModel?
    @State private var showDeleteAlert = false

    private var watch: PriceWatch? { viewModel?.selectedWatch }

    var body: some View {
        Group {
            if let watch {
                watchDetail(watch)
            } else if viewModel?.isLoading == true {
                LoadingView()
            } else if let error = viewModel?.error {
                ErrorView(message: error) {
                    Task { await viewModel?.fetchWatch(id: watchId) }
                }
            } else {
                LoadingView()
            }
        }
        .navigationTitle("Watch Details")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .task {
            if viewModel == nil { viewModel = WatchesViewModel(api: api) }
            if alertsVM == nil { alertsVM = AlertsViewModel(api: api) }
            if priceVM == nil { priceVM = PriceHistoryViewModel(api: api) }
            await viewModel?.fetchWatch(id: watchId)
            await alertsVM?.fetchWatchAlerts(watchId: watchId)
        }
    }

    @ViewBuilder
    private func watchDetail(_ watch: PriceWatch) -> some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                // Info card
                watchInfoCard(watch)

                // Actions
                actionButtons(watch)

                // Price chart (need trip ID)
                if let priceVM, !priceVM.snapshots.isEmpty {
                    Text("Price History")
                        .font(.headline)
                        .padding(.horizontal)
                    PriceChartView(snapshots: priceVM.snapshots)
                        .frame(height: 200)
                        .padding(.horizontal)
                }

                // Alert history
                if let alertsVM {
                    Text("Alert History")
                        .font(.headline)
                        .padding(.horizontal)
                    if alertsVM.alerts.isEmpty {
                        Text("No alerts triggered yet.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .padding(.horizontal)
                    } else {
                        AlertListContent(alerts: alertsVM.alerts)
                            .padding(.horizontal)
                    }
                }
            }
            .padding(.vertical)
        }
        .refreshable {
            await viewModel?.fetchWatch(id: watchId)
            await alertsVM?.fetchWatchAlerts(watchId: watchId)
        }
        .alert("Delete Watch?", isPresented: $showDeleteAlert) {
            Button("Delete", role: .destructive) {
                Task {
                    let success = await viewModel?.deleteWatch(id: watchId) ?? false
                    if success { dismiss() }
                }
            }
            Button("Cancel", role: .cancel) {}
        }
        .task(id: watch.tripId) {
            await priceVM?.fetchPrices(tripId: watch.tripId, provider: watch.provider)
        }
    }

    private func watchInfoCard(_ watch: PriceWatch) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Image(systemName: "eye.fill")
                    .font(.title2)
                    .foregroundStyle(.blue)
                VStack(alignment: .leading) {
                    Text(watch.provider.replacingOccurrences(of: "_", with: " ").capitalized)
                        .font(.headline)
                }
                Spacer()
                StatusBadge(
                    text: watch.isActive ? "Active" : "Paused",
                    variant: watch.isActive ? .success : .default
                )
            }

            Divider()

            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("Target Price")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text(Formatters.price(cents: watch.targetPrice, currency: watch.currency))
                        .font(.title2)
                        .fontWeight(.bold)
                        .foregroundStyle(.green)
                }
                Spacer()
                VStack(alignment: .trailing, spacing: 4) {
                    Text("Cooldown")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                    Text("\(watch.alertCooldownHours) hours")
                        .font(.subheadline)
                }
            }

            HStack {
                Label("Created \(Formatters.displayDate(watch.createdAt))", systemImage: "calendar")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
        .padding(.horizontal)
    }

    private func actionButtons(_ watch: PriceWatch) -> some View {
        HStack(spacing: 12) {
            Button {
                Task {
                    let success = await viewModel?.toggleActive(id: watch.id, currentlyActive: watch.isActive) ?? false
                    if success {
                        await viewModel?.fetchWatch(id: watchId)
                    }
                }
            } label: {
                Label(
                    watch.isActive ? "Pause" : "Resume",
                    systemImage: watch.isActive ? "pause.fill" : "play.fill"
                )
            }
            .buttonStyle(.bordered)

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
