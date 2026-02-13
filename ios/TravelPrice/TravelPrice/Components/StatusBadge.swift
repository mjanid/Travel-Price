import SwiftUI

/// A colored badge for displaying status (active, paused, sent, etc.).
struct StatusBadge: View {
    let text: String
    let variant: Variant

    enum Variant {
        case success, danger, warning, `default`

        var backgroundColor: Color {
            switch self {
            case .success: return .green.opacity(0.15)
            case .danger: return .red.opacity(0.15)
            case .warning: return .orange.opacity(0.15)
            case .default: return .gray.opacity(0.15)
            }
        }

        var foregroundColor: Color {
            switch self {
            case .success: return .green
            case .danger: return .red
            case .warning: return .orange
            case .default: return .gray
            }
        }
    }

    var body: some View {
        Text(text)
            .font(.caption)
            .fontWeight(.medium)
            .padding(.horizontal, 8)
            .padding(.vertical, 3)
            .background(variant.backgroundColor, in: Capsule())
            .foregroundStyle(variant.foregroundColor)
    }
}

/// Badge specifically for price display.
struct PriceBadge: View {
    let cents: Int
    let currency: String

    var body: some View {
        Text(Formatters.price(cents: cents, currency: currency))
            .font(.headline)
            .fontWeight(.bold)
            .foregroundStyle(.primary)
    }
}
