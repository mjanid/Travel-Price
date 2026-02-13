import SwiftUI

/// Form for creating a new price watch.
struct WatchFormView: View {
    @Environment(\.dismiss) private var dismiss
    let viewModel: WatchesViewModel
    let tripId: String

    @State private var targetPriceDollars = ""
    @State private var currency = "USD"
    @State private var cooldownHours = 6
    @State private var provider = "google_flights"
    @State private var isSaving = false

    private let currencies = ["USD", "EUR", "GBP", "CHF", "JPY", "CAD", "AUD"]

    private var isFormValid: Bool {
        Validators.isValidTargetPrice(targetPriceDollars)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Price Target") {
                    HStack {
                        Text(currencySymbol)
                            .foregroundStyle(.secondary)
                        TextField("Target price", text: $targetPriceDollars)
                            #if os(iOS)
                            .keyboardType(.decimalPad)
                            #endif
                    }

                    Picker("Currency", selection: $currency) {
                        ForEach(currencies, id: \.self) { cur in
                            Text(cur).tag(cur)
                        }
                    }
                }

                Section("Provider") {
                    Picker("Provider", selection: $provider) {
                        Text("Google Flights").tag("google_flights")
                    }
                }

                Section("Alert Settings") {
                    Stepper("Cooldown: \(cooldownHours) hours", value: $cooldownHours, in: 1...168)
                    Text("Minimum time between alerts for this watch.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                if let error = viewModel.error {
                    Section {
                        Text(error)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle("New Price Watch")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Create") {
                        Task { await save() }
                    }
                    .disabled(!isFormValid || isSaving)
                }
            }
        }
    }

    private var currencySymbol: String {
        switch currency {
        case "USD", "CAD", "AUD": return "$"
        case "EUR": return "\u{20AC}"
        case "GBP": return "\u{00A3}"
        case "CHF": return "CHF"
        case "JPY": return "\u{00A5}"
        default: return currency
        }
    }

    private func save() async {
        isSaving = true
        defer { isSaving = false }

        guard let cents = Formatters.dollarsToCents(targetPriceDollars) else { return }

        let request = WatchCreateRequest(
            tripId: tripId,
            provider: provider,
            targetPrice: cents,
            currency: currency,
            alertCooldownHours: cooldownHours
        )

        let watch = await viewModel.createWatch(request)
        if watch != nil { dismiss() }
    }
}
