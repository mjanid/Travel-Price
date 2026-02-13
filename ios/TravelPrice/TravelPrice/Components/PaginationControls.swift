import SwiftUI

/// Reusable pagination controls with Previous/Next buttons and page info.
struct PaginationControls: View {
    let currentPage: Int
    let totalPages: Int
    let onPrevious: () -> Void
    let onNext: () -> Void

    var body: some View {
        if totalPages > 1 {
            HStack {
                Button {
                    onPrevious()
                } label: {
                    Label("Previous", systemImage: "chevron.left")
                }
                .disabled(currentPage <= 1)

                Spacer()

                Text("Page \(currentPage) of \(totalPages)")
                    .font(.caption)
                    .foregroundStyle(.secondary)

                Spacer()

                Button {
                    onNext()
                } label: {
                    Label("Next", systemImage: "chevron.right")
                        .labelStyle(.trailingIcon)
                }
                .disabled(currentPage >= totalPages)
            }
            .padding(.horizontal)
            .padding(.vertical, 8)
        }
    }
}

/// Custom label style to show icon after text.
private struct TrailingIconLabelStyle: LabelStyle {
    func makeBody(configuration: Configuration) -> some View {
        HStack(spacing: 4) {
            configuration.title
            configuration.icon
        }
    }
}

extension LabelStyle where Self == TrailingIconLabelStyle {
    static var trailingIcon: TrailingIconLabelStyle { .init() }
}
