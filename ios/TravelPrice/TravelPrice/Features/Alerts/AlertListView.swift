import SwiftUI

struct AlertListView: View {
    @Environment(APIClient.self) private var api
    @State private var viewModel: AlertsViewModel?

    var body: some View {
        NavigationStack {
            Group {
                if let vm = viewModel {
                    alertContent(vm)
                } else {
                    LoadingView()
                }
            }
            .navigationTitle("Alerts")
            .task {
                if viewModel == nil {
                    viewModel = AlertsViewModel(api: api)
                }
                await viewModel?.fetchAlerts()
            }
        }
    }

    @ViewBuilder
    private func alertContent(_ vm: AlertsViewModel) -> some View {
        if vm.isLoading && vm.alerts.isEmpty {
            LoadingView()
        } else if let error = vm.error, vm.alerts.isEmpty {
            ErrorView(message: error) {
                Task { await vm.fetchAlerts() }
            }
        } else if vm.alerts.isEmpty {
            emptyState
        } else {
            List {
                AlertListContent(alerts: vm.alerts)

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
                await vm.fetchAlerts(page: vm.currentPage)
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "bell.slash")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("No Alerts Yet")
                .font(.title3)
                .fontWeight(.semibold)
            Text("Alerts appear when prices drop below your watch targets.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}

/// Reusable alert list content (used in both AlertListView and WatchDetailView).
struct AlertListContent: View {
    let alerts: [PriceAlert]

    var body: some View {
        ForEach(alerts) { alert in
            alertRow(alert)
        }
    }

    private func alertRow(_ alert: PriceAlert) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "bell.fill")
                    .foregroundStyle(.orange)
                Text(alert.alertType.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Spacer()
                StatusBadge(
                    text: alert.status.capitalized,
                    variant: alert.status == "sent" ? .success : .default
                )
            }

            HStack(spacing: 16) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Target")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text(Formatters.price(cents: alert.targetPrice))
                        .font(.caption)
                }
                VStack(alignment: .leading, spacing: 2) {
                    Text("Triggered at")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Text(Formatters.price(cents: alert.triggeredPrice))
                        .font(.caption)
                        .foregroundStyle(.green)
                }
                if alert.savingsCents > 0 {
                    VStack(alignment: .leading, spacing: 2) {
                        Text("Savings")
                            .font(.caption2)
                            .foregroundStyle(.secondary)
                        Text(Formatters.price(cents: alert.savingsCents))
                            .font(.caption)
                            .fontWeight(.bold)
                            .foregroundStyle(.green)
                    }
                }
            }

            if let message = alert.message {
                Text(message)
                    .font(.caption)
                    .foregroundStyle(.secondary)
                    .lineLimit(2)
            }

            Text(Formatters.displayDateTime(alert.createdAt))
                .font(.caption2)
                .foregroundStyle(.secondary)
        }
        .padding(.vertical, 4)
    }
}
