import SwiftUI
import Charts

/// Line chart showing price history over time.
struct PriceChartView: View {
    let snapshots: [PriceSnapshot]

    private var chartData: [(date: Date, price: Double)] {
        snapshots.compactMap { snap in
            guard let date = Formatters.parseISO(snap.scrapedAt) else { return nil }
            return (date: date, price: snap.priceInDollars)
        }
        .sorted { $0.date < $1.date }
    }

    private var priceRange: ClosedRange<Double> {
        let prices = chartData.map(\.price)
        guard let min = prices.min(), let max = prices.max() else { return 0...100 }
        let padding = (max - min) * 0.1
        return (min - padding)...(max + padding)
    }

    var body: some View {
        if chartData.isEmpty {
            Text("No price data yet")
                .font(.subheadline)
                .foregroundStyle(.secondary)
                .frame(maxWidth: .infinity, minHeight: 100)
        } else {
            Chart(chartData, id: \.date) { point in
                LineMark(
                    x: .value("Date", point.date),
                    y: .value("Price", point.price)
                )
                .foregroundStyle(.blue)
                .interpolationMethod(.catmullRom)

                PointMark(
                    x: .value("Date", point.date),
                    y: .value("Price", point.price)
                )
                .foregroundStyle(.blue)
                .symbolSize(20)
            }
            .chartYScale(domain: priceRange)
            .chartYAxis {
                AxisMarks(position: .leading) { value in
                    AxisGridLine()
                    AxisValueLabel {
                        if let dollars = value.as(Double.self) {
                            Text("$\(Int(dollars))")
                                .font(.caption2)
                        }
                    }
                }
            }
            .chartXAxis {
                AxisMarks { value in
                    AxisGridLine()
                    AxisValueLabel {
                        if let date = value.as(Date.self) {
                            Text(date, format: .dateTime.month(.abbreviated).day())
                                .font(.caption2)
                        }
                    }
                }
            }
        }
    }
}
