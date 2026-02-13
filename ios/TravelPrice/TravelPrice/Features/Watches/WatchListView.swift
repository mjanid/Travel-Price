import SwiftUI

struct WatchListView: View {
    @Environment(APIClient.self) private var api
    @State private var viewModel: WatchesViewModel?

    var body: some View {
        NavigationStack {
            Group {
                if let vm = viewModel {
                    watchContent(vm)
                } else {
                    LoadingView()
                }
            }
            .navigationTitle("Price Watches")
            .task {
                if viewModel == nil {
                    viewModel = WatchesViewModel(api: api)
                }
                await viewModel?.fetchWatches()
            }
        }
    }

    @ViewBuilder
    private func watchContent(_ vm: WatchesViewModel) -> some View {
        if vm.isLoading && vm.watches.isEmpty {
            LoadingView()
        } else if let error = vm.error, vm.watches.isEmpty {
            ErrorView(message: error) {
                Task { await vm.fetchWatches() }
            }
        } else if vm.watches.isEmpty {
            emptyState
        } else {
            List {
                ForEach(vm.watches) { watch in
                    NavigationLink(value: watch.id) {
                        WatchCardView(watch: watch)
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
                await vm.fetchWatches(page: vm.currentPage)
            }
            .navigationDestination(for: String.self) { watchId in
                WatchDetailView(watchId: watchId)
            }
        }
    }

    private var emptyState: some View {
        VStack(spacing: 16) {
            Image(systemName: "eye.slash")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("No Price Watches")
                .font(.title3)
                .fontWeight(.semibold)
            Text("Add a price watch from a trip detail page to start getting alerts.")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
    }
}
