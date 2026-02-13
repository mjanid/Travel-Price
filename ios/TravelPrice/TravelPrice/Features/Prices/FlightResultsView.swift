import SwiftUI

/// Table/List of recent flight scrape results.
struct FlightResultsView: View {
    let snapshots: [PriceSnapshot]

    /// Show only the most recent scrape batch (same scrapedAt timestamp).
    private var latestResults: [PriceSnapshot] {
        guard let latest = snapshots.first?.scrapedAt else { return [] }
        return snapshots.filter { $0.scrapedAt == latest }
    }

    var body: some View {
        if latestResults.isEmpty {
            Text("No flight results yet")
                .font(.subheadline)
                .foregroundStyle(.secondary)
        } else {
            VStack(spacing: 0) {
                // Header row
                HStack(spacing: 4) {
                    Text("Airline").font(.caption).fontWeight(.semibold)
                        .frame(maxWidth: .infinity, alignment: .leading)
                    Text("Duration").font(.caption).fontWeight(.semibold)
                        .frame(width: 70)
                    Text("Dep").font(.caption).fontWeight(.semibold)
                        .frame(width: 64)
                    Text("Arr").font(.caption).fontWeight(.semibold)
                        .frame(width: 64)
                    Text("Stops").font(.caption).fontWeight(.semibold)
                        .frame(width: 44)
                    Text("Price").font(.caption).fontWeight(.semibold)
                        .frame(width: 70, alignment: .trailing)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)
                .background(Color.gray.opacity(0.12))

                Divider()

                ForEach(latestResults) { snap in
                    flightRow(snap)
                    Divider()
                }
            }
            .clipShape(RoundedRectangle(cornerRadius: 8))
            .overlay(
                RoundedRectangle(cornerRadius: 8)
                    .stroke(Color.gray.opacity(0.2), lineWidth: 1)
            )
        }
    }

    private func flightRow(_ snap: PriceSnapshot) -> some View {
        HStack(spacing: 4) {
            Text(snap.displayAirline)
                .font(.caption)
                .lineLimit(1)
                .frame(maxWidth: .infinity, alignment: .leading)

            Text(snap.displayDuration)
                .font(.caption)
                .foregroundStyle(.secondary)
                .lineLimit(1)
                .frame(width: 70)

            Text(snap.displayDepartureTime)
                .font(.caption)
                .lineLimit(1)
                .frame(width: 64)

            Text(snap.displayArrivalTime)
                .font(.caption)
                .lineLimit(1)
                .frame(width: 64)

            Text(snap.displayStops)
                .font(.caption)
                .frame(width: 44)

            Text(Formatters.price(cents: snap.price, currency: snap.currency))
                .font(.caption)
                .fontWeight(.medium)
                .frame(width: 70, alignment: .trailing)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 6)
    }
}
