import SwiftUI

struct SettingsView: View {
    @Environment(APIClient.self) private var api
    @Environment(AuthViewModel.self) private var auth

    @State private var serverURL: String = ""
    @State private var isTestingConnection = false
    @State private var connectionStatus: ConnectionStatus?

    @State private var fullName: String = ""
    @State private var newPassword: String = ""
    @State private var confirmPassword: String = ""
    @State private var isSavingProfile = false
    @State private var profileMessage: String?

    enum ConnectionStatus {
        case success, failure(String)
    }

    var body: some View {
        NavigationStack {
            Form {
                serverSection
                profileSection
                passwordSection
                accountSection
                logoutSection
            }
            .navigationTitle("Settings")
            .onAppear {
                serverURL = api.baseURL
                fullName = auth.currentUser?.fullName ?? ""
            }
        }
    }

    // MARK: - Server Configuration

    private var serverSection: some View {
        Section {
            TextField("Server URL", text: $serverURL)
                .autocorrectionDisabled()
                #if os(iOS)
                .textInputAutocapitalization(.never)
                .keyboardType(.URL)
                #endif

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
                .disabled(isTestingConnection || serverURL.isEmpty)

                Spacer()

                if let status = connectionStatus {
                    switch status {
                    case .success:
                        Label("Connected", systemImage: "checkmark.circle.fill")
                            .foregroundStyle(.green)
                            .font(.caption)
                    case .failure(let msg):
                        Label(msg, systemImage: "xmark.circle.fill")
                            .foregroundStyle(.red)
                            .font(.caption)
                    }
                }
            }
        } header: {
            Text("Server")
        } footer: {
            Text("Enter your backend server URL (e.g., http://192.168.1.50:8000)")
        }
    }

    // MARK: - Profile

    private var profileSection: some View {
        Section("Profile") {
            TextField("Full Name", text: $fullName)
            Text(auth.currentUser?.email ?? "")
                .foregroundStyle(.secondary)

            Button {
                Task { await saveProfile() }
            } label: {
                if isSavingProfile {
                    ProgressView()
                        .controlSize(.small)
                } else {
                    Text("Save Name")
                }
            }
            .disabled(fullName.isEmpty || isSavingProfile)

            if let msg = profileMessage {
                Text(msg)
                    .font(.caption)
                    .foregroundStyle(msg.contains("Error") ? .red : .green)
            }
        }
    }

    // MARK: - Password

    private var passwordSection: some View {
        Section("Change Password") {
            SecureField("New Password (8+ characters)", text: $newPassword)
            SecureField("Confirm Password", text: $confirmPassword)

            if !confirmPassword.isEmpty && newPassword != confirmPassword {
                Text("Passwords don't match")
                    .font(.caption)
                    .foregroundStyle(.red)
            }

            Button("Update Password") {
                Task { await updatePassword() }
            }
            .disabled(
                !Validators.isValidPassword(newPassword)
                    || newPassword != confirmPassword
                    || isSavingProfile
            )
        }
    }

    // MARK: - Account Info

    private var accountSection: some View {
        Section("Account") {
            if let user = auth.currentUser {
                LabeledContent("Account ID", value: String(user.id.prefix(8)) + "...")
                LabeledContent("Member Since", value: Formatters.displayDate(user.createdAt))
                LabeledContent("Status", value: user.isActive ? "Active" : "Inactive")
            }
        }
    }

    // MARK: - Logout

    private var logoutSection: some View {
        Section {
            Button("Sign Out", role: .destructive) {
                auth.logout()
            }
        }
    }

    // MARK: - Actions

    private func testConnection() async {
        isTestingConnection = true
        defer { isTestingConnection = false }

        do {
            let ok = try await api.testConnection()
            connectionStatus = ok ? .success : .failure("Not reachable")
        } catch {
            connectionStatus = .failure("Failed")
        }
    }

    private func saveProfile() async {
        isSavingProfile = true
        profileMessage = nil
        defer { isSavingProfile = false }

        await auth.updateProfile(fullName: fullName)
        if auth.error != nil {
            profileMessage = "Error: \(auth.error ?? "Unknown")"
        } else {
            profileMessage = "Profile updated!"
        }
    }

    private func updatePassword() async {
        isSavingProfile = true
        profileMessage = nil
        defer { isSavingProfile = false }

        await auth.updateProfile(password: newPassword)
        if auth.error != nil {
            profileMessage = "Error: \(auth.error ?? "Unknown")"
        } else {
            profileMessage = "Password updated!"
            newPassword = ""
            confirmPassword = ""
        }
    }
}
