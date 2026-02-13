import SwiftUI

/// A card displaying trip summary info.
struct TripCardView: View {
    let trip: Trip

    private var isPast: Bool {
        guard let date = Formatters.parseDate(trip.departureDate) else { return false }
        return date < Date()
    }

    private var tripType: TripType {
        TripType(rawValue: trip.tripType) ?? .flight
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Route
            HStack {
                Image(systemName: tripType.icon)
                    .foregroundStyle(.blue)
                Text(trip.origin)
                    .font(.headline)
                    .fontWeight(.bold)
                Image(systemName: "arrow.right")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(trip.destination)
                    .font(.headline)
                    .fontWeight(.bold)

                Spacer()

                StatusBadge(
                    text: isPast ? "Past" : "Upcoming",
                    variant: isPast ? .default : .success
                )
            }

            // Dates
            HStack(spacing: 16) {
                Label(Formatters.displayDate(trip.departureDate), systemImage: "calendar")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)

                if let returnDate = trip.returnDate {
                    Label(Formatters.displayDate(returnDate), systemImage: "calendar.badge.clock")
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                }
            }

            // Travelers
            HStack(spacing: 16) {
                Label("\(trip.travelers) traveler\(trip.travelers == 1 ? "" : "s")",
                      systemImage: "person.fill")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Text(tripType.displayName)
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .shadow(color: .black.opacity(0.05), radius: 4, y: 2)
    }
}
