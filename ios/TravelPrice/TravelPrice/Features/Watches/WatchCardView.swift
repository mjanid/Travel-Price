import SwiftUI

/// Card displaying price watch summary.
struct WatchCardView: View {
    let watch: PriceWatch

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack {
                Image(systemName: "eye.fill")
                    .foregroundStyle(.blue)
                Text(watch.provider.replacingOccurrences(of: "_", with: " ").capitalized)
                    .font(.subheadline)
                    .fontWeight(.medium)
                Spacer()
                StatusBadge(
                    text: watch.isActive ? "Active" : "Paused",
                    variant: watch.isActive ? .success : .default
                )
            }

            HStack {
                Text("Target:")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text(Formatters.price(cents: watch.targetPrice, currency: watch.currency))
                    .font(.subheadline)
                    .fontWeight(.bold)
                    .foregroundStyle(.green)
            }

            HStack(spacing: 12) {
                Label("\(watch.alertCooldownHours)h cooldown", systemImage: "clock")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                Label(watch.currency, systemImage: "dollarsign.circle")
                    .font(.caption2)
                    .foregroundStyle(.secondary)
            }
        }
        .padding()
        .background(.background)
        .clipShape(RoundedRectangle(cornerRadius: 10))
        .shadow(color: .black.opacity(0.04), radius: 3, y: 1)
    }
}
