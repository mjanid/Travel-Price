import SwiftUI

struct RegisterView: View {
    @Environment(AuthViewModel.self) private var auth
    @Environment(APIClient.self) private var api
    @Environment(\.dismiss) private var dismiss
    @State private var email = ""
    @State private var password = ""
    @State private var confirmPassword = ""
    @State private var fullName = ""
    @State private var showServerConfig = false
    @State private var serverURL = ""
    @State private var isTestingConnection = false
    @State private var connectionOK: Bool?

    private var isFormValid: Bool {
        Validators.isValidEmail(email)
            && Validators.isValidPassword(password)
            && password == confirmPassword
            && Validators.isValidFullName(fullName)
    }

    private var passwordMismatch: Bool {
        !confirmPassword.isEmpty && password != confirmPassword
    }

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            VStack(spacing: 8) {
                Text("Create Account")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                Text("Start tracking travel prices")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }

            VStack(spacing: 16) {
                TextField("Full Name", text: $fullName)
                    .textContentType(.name)
                    #if os(iOS)
                    .textFieldStyle(.roundedBorder)
                    #endif

                TextField("Email", text: $email)
                    .textContentType(.emailAddress)
                    .autocorrectionDisabled()
                    #if os(iOS)
                    .keyboardType(.emailAddress)
                    .textInputAutocapitalization(.never)
                    .textFieldStyle(.roundedBorder)
                    #endif

                SecureField("Password (8+ characters)", text: $password)
                    .textContentType(.newPassword)
                    #if os(iOS)
                    .textFieldStyle(.roundedBorder)
                    #endif

                SecureField("Confirm Password", text: $confirmPassword)
                    .textContentType(.newPassword)
                    #if os(iOS)
                    .textFieldStyle(.roundedBorder)
                    #endif

                if passwordMismatch {
                    Text("Passwords don't match")
                        .font(.caption)
                        .foregroundStyle(.red)
                }

                if let error = auth.error {
                    Text(error)
                        .font(.caption)
                        .foregroundStyle(.red)
                        .multilineTextAlignment(.center)
                }

                Button {
                    Task {
                        await auth.register(
                            email: email,
                            password: password,
                            fullName: fullName
                        )
                    }
                } label: {
                    if auth.isLoading {
                        ProgressView()
                            .frame(maxWidth: .infinity)
                    } else {
                        Text("Create Account")
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
        }
        .navigationTitle("Register")
        #if os(iOS)
        .navigationBarTitleDisplayMode(.inline)
        #endif
        .onAppear {
            serverURL = api.baseURL
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
