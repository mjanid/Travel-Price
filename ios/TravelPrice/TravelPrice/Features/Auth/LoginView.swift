import SwiftUI

struct LoginView: View {
    @Environment(AuthViewModel.self) private var auth
    @Environment(APIClient.self) private var api
    @State private var email = ""
    @State private var password = ""
    @State private var showRegister = false
    @State private var showServerConfig = false
    @State private var serverURL = ""
    @State private var isTestingConnection = false
    @State private var connectionOK: Bool?

    private var isFormValid: Bool {
        Validators.isValidEmail(email) && Validators.isValidPassword(password)
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 24) {
                Spacer()

                // Header
                VStack(spacing: 8) {
                    Image(systemName: "airplane.circle.fill")
                        .font(.system(size: 60))
                        .foregroundStyle(.blue)
                    Text("Travel Price")
                        .font(.largeTitle)
                        .fontWeight(.bold)
                    Text("Monitor prices. Get alerts.")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }

                // Form
                VStack(spacing: 16) {
                    TextField("Email", text: $email)
                        .textContentType(.emailAddress)
                        .autocorrectionDisabled()
                        #if os(iOS)
                        .keyboardType(.emailAddress)
                        .textInputAutocapitalization(.never)
                        .textFieldStyle(.roundedBorder)
                        #endif

                    SecureField("Password", text: $password)
                        .textContentType(.password)
                        #if os(iOS)
                        .textFieldStyle(.roundedBorder)
                        #endif

                    if let error = auth.error {
                        Text(error)
                            .font(.caption)
                            .foregroundStyle(.red)
                            .multilineTextAlignment(.center)
                    }

                    Button {
                        Task {
                            await auth.login(email: email, password: password)
                        }
                    } label: {
                        if auth.isLoading {
                            ProgressView()
                                .frame(maxWidth: .infinity)
                        } else {
                            Text("Sign In")
                                .frame(maxWidth: .infinity)
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                    .disabled(!isFormValid || auth.isLoading)
                }
                .padding(.horizontal, 32)

                // Server configuration
                serverConfigSection
                    .padding(.horizontal, 32)

                Spacer()

                // Register link
                HStack {
                    Text("Don't have an account?")
                        .foregroundStyle(.secondary)
                    Button("Create one") {
                        showRegister = true
                    }
                }
                .font(.subheadline)
                .padding(.bottom)
            }
            .navigationDestination(isPresented: $showRegister) {
                RegisterView()
            }
            .onAppear {
                serverURL = api.baseURL
            }
        }
    }

    // MARK: - Server Config

    private var serverConfigSection: some View {
        DisclosureGroup("Server", isExpanded: $showServerConfig) {
            VStack(spacing: 8) {
                TextField("http://192.168.1.X:8000", text: $serverURL)
                    .autocorrectionDisabled()
                    #if os(iOS)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.URL)
                    .textFieldStyle(.roundedBorder)
                    #endif
                    .onSubmit { api.baseURL = serverURL }

                HStack {
                    Button {
                        api.baseURL = serverURL
                        Task { await testConnection() }
                    } label: {
                        if isTestingConnection {
                            ProgressView()
                                .controlSize(.small)
                        } else {
                            Text("Test Connection")
                        }
                    }
                    .buttonStyle(.bordered)
                    .controlSize(.small)
                    .disabled(isTestingConnection || serverURL.isEmpty)

                    Spacer()

                    if let ok = connectionOK {
                        Label(
                            ok ? "Connected" : "Failed",
                            systemImage: ok ? "checkmark.circle.fill" : "xmark.circle.fill"
                        )
                        .foregroundStyle(ok ? .green : .red)
                        .font(.caption)
                    }
                }
            }
            .padding(.top, 8)
        }
        .font(.subheadline)
        .foregroundStyle(.secondary)
    }

    private func testConnection() async {
        isTestingConnection = true
        connectionOK = nil
        defer { isTestingConnection = false }
        do {
            connectionOK = try await api.testConnection()
        } catch {
            connectionOK = false
        }
    }
}
