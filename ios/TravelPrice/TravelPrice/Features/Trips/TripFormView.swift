import SwiftUI

/// Reusable form for creating or editing a trip.
struct TripFormView: View {
    @Environment(\.dismiss) private var dismiss
    let viewModel: TripsViewModel

    /// If editing, pass the existing trip.
    var editingTrip: Trip?

    @State private var origin = ""
    @State private var destination = ""
    @State private var departureDate = Date()
    @State private var returnDate: Date?
    @State private var hasReturnDate = false
    @State private var travelers = 1
    @State private var tripType: TripType = .flight
    @State private var notes = ""
    @State private var isSaving = false

    private var isEditing: Bool { editingTrip != nil }

    private var isFormValid: Bool {
        Validators.isValidIATA(origin)
            && Validators.isValidIATA(destination)
            && origin.uppercased() != destination.uppercased()
            && Validators.isValidNotes(notes)
    }

    var body: some View {
        NavigationStack {
            Form {
                Section("Route") {
                    HStack {
                        TextField("Origin (e.g. JFK)", text: $origin)
                            .autocorrectionDisabled()
                            #if os(iOS)
                            .textInputAutocapitalization(.characters)
                            #endif
                            .onChange(of: origin) { _, newVal in
                                origin = Formatters.iataCode(newVal)
                            }

                        Image(systemName: "arrow.right")
                            .foregroundStyle(.secondary)

                        TextField("Destination (e.g. LAX)", text: $destination)
                            .autocorrectionDisabled()
                            #if os(iOS)
                            .textInputAutocapitalization(.characters)
                            #endif
                            .onChange(of: destination) { _, newVal in
                                destination = Formatters.iataCode(newVal)
                            }
                    }
                }

                Section("Dates") {
                    DatePicker("Departure", selection: $departureDate, displayedComponents: .date)

                    Toggle("Round Trip", isOn: $hasReturnDate)

                    if hasReturnDate {
                        DatePicker(
                            "Return",
                            selection: Binding(
                                get: { returnDate ?? departureDate.addingTimeInterval(86400 * 7) },
                                set: { returnDate = $0 }
                            ),
                            in: departureDate...,
                            displayedComponents: .date
                        )
                    }
                }

                Section("Details") {
                    Stepper("Travelers: \(travelers)", value: $travelers, in: 1...20)

                    Picker("Trip Type", selection: $tripType) {
                        ForEach(TripType.allCases, id: \.self) { type in
                            Label(type.displayName, systemImage: type.icon)
                                .tag(type)
                        }
                    }
                }

                Section("Notes") {
                    TextEditor(text: $notes)
                        .frame(minHeight: 80)
                    if notes.count > 1800 {
                        Text("\(notes.count)/2000 characters")
                            .font(.caption)
                            .foregroundStyle(notes.count > 2000 ? .red : .secondary)
                    }
                }

                if let error = viewModel.error {
                    Section {
                        Text(error)
                            .foregroundStyle(.red)
                    }
                }
            }
            .navigationTitle(isEditing ? "Edit Trip" : "New Trip")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button(isEditing ? "Save" : "Create") {
                        Task { await save() }
                    }
                    .disabled(!isFormValid || isSaving)
                }
            }
            .onAppear(perform: populateFromTrip)
        }
    }

    // MARK: - Actions

    private func populateFromTrip() {
        guard let trip = editingTrip else { return }
        origin = trip.origin
        destination = trip.destination
        if let d = Formatters.parseDate(trip.departureDate) {
            departureDate = d
        }
        if let rd = trip.returnDate, let d = Formatters.parseDate(rd) {
            returnDate = d
            hasReturnDate = true
        }
        travelers = trip.travelers
        tripType = TripType(rawValue: trip.tripType) ?? .flight
        notes = trip.notes ?? ""
    }

    private func save() async {
        isSaving = true
        defer { isSaving = false }

        let returnDateStr = hasReturnDate
            ? Formatters.apiDate(returnDate ?? departureDate.addingTimeInterval(86400 * 7))
            : nil

        if isEditing, let trip = editingTrip {
            let request = TripUpdateRequest(
                origin: origin.uppercased(),
                destination: destination.uppercased(),
                departureDate: Formatters.apiDate(departureDate),
                returnDate: returnDateStr,
                travelers: travelers,
                tripType: tripType.rawValue,
                notes: notes.isEmpty ? nil : notes
            )
            let success = await viewModel.updateTrip(id: trip.id, request)
            if success { dismiss() }
        } else {
            var request = TripCreateRequest(
                origin: origin.uppercased(),
                destination: destination.uppercased(),
                departureDate: Formatters.apiDate(departureDate)
            )
            request.returnDate = returnDateStr
            request.travelers = travelers
            request.tripType = tripType.rawValue
            request.notes = notes.isEmpty ? nil : notes

            let trip = await viewModel.createTrip(request)
            if trip != nil { dismiss() }
        }
    }
}
