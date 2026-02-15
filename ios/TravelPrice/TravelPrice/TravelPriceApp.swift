import SwiftUI

@main
struct TravelPriceApp: App {
    @State private var apiClient = APIClient()
    @State private var authViewModel: AuthViewModel

    init() {
        let api = APIClient()
        _apiClient = State(initialValue: api)
        _authViewModel = State(initialValue: AuthViewModel(api: api))
    }

    var body: some Scene {
        WindowGroup {
            RootView()
                .environment(apiClient)
                .environment(authViewModel)
        }
    }
}

/// Root view that switches between auth and main content.
struct RootView: View {
    @Environment(AuthViewModel.self) private var auth

    var body: some View {
        Group {
            if auth.isLoading && auth.currentUser == nil {
                LoadingView(message: "Connecting...")
            } else if auth.isAuthenticated {
                MainTabView()
            } else {
                LoginView()
            }
        }
        .task {
            await auth.checkSession()
        }
    }
}

/// Main navigation after authentication.
struct MainTabView: View {
    var body: some View {
        #if os(iOS)
        TabView {
            DashboardView()
                .tabItem { Label("Dashboard", systemImage: "square.grid.2x2") }
            TripListView()
                .tabItem { Label("Trips", systemImage: "airplane") }
            WatchListView()
                .tabItem { Label("Watches", systemImage: "eye") }
            AlertListView()
                .tabItem { Label("Alerts", systemImage: "bell") }
            SettingsView()
                .tabItem { Label("Settings", systemImage: "gear") }
        }
        #else
        MacSidebarView()
        #endif
    }
}

#if os(macOS)
enum SidebarItem: String, CaseIterable, Hashable {
    case dashboard, trips, watches, alerts, settings

    var title: String {
        rawValue.capitalized
    }

    var icon: String {
        switch self {
        case .dashboard: return "square.grid.2x2"
        case .trips: return "airplane"
        case .watches: return "eye"
        case .alerts: return "bell"
        case .settings: return "gear"
        }
    }
}

struct MacSidebarView: View {
    @State private var selection: SidebarItem? = .dashboard

    var body: some View {
        NavigationSplitView {
            List(SidebarItem.allCases, id: \.self, selection: $selection) { item in
                Label(item.title, systemImage: item.icon)
            }
            .navigationTitle("Travel Price")
        } detail: {
            switch selection {
            case .dashboard, .none:
                DashboardView()
            case .trips:
                TripListView()
            case .watches:
                WatchListView()
            case .alerts:
                AlertListView()
            case .settings:
                SettingsView()
            }
        }
    }
}
#endif
