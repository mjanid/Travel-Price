import Foundation

struct Trip: Codable, Identifiable {
    let id: String
    let userId: String
    let origin: String
    let destination: String
    let departureDate: String
    let returnDate: String?
    let travelers: Int
    let tripType: String
    let notes: String?
    let createdAt: String
    let updatedAt: String
}

// MARK: - Request Models

struct TripCreateRequest: Encodable {
    let origin: String
    let destination: String
    let departureDate: String
    var returnDate: String?
    var travelers: Int = 1
    var tripType: String = "flight"
    var notes: String?
}

struct TripUpdateRequest: Encodable {
    var origin: String?
    var destination: String?
    var departureDate: String?
    var returnDate: String?
    var travelers: Int?
    var tripType: String?
    var notes: String?
}

// MARK: - Trip Type

enum TripType: String, CaseIterable {
    case flight
    case hotel
    case carRental = "car_rental"

    var displayName: String {
        switch self {
        case .flight: return "Flight"
        case .hotel: return "Hotel"
        case .carRental: return "Car Rental"
        }
    }

    var icon: String {
        switch self {
        case .flight: return "airplane"
        case .hotel: return "building.2"
        case .carRental: return "car"
        }
    }
}
